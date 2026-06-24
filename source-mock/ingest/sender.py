"""POST /ingest with auth, retry/backoff, and status handling."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from . import ledger
from .transport import get_header, http_post as _default_http_post

# Max network attempts for retryable statuses (429 / 5xx).
_MAX_BACKOFF_ATTEMPTS = 3
_BACKOFF_BASE = 0.5

_SCOPE_HINT = (
    'token lacks `write` scope — re-register the client with '
    '--scopes "read write" (the bare register-client defaults to read only)'
)


@dataclass
class SendOutcome:
    result: str                    # sent | too_large | error
    http_status: int | None = None
    job_id: str | None = None
    server_content_hash: str | None = None
    error: str | None = None


def _backoff_seconds(resp, attempt: int) -> float:
    """Honor server pacing headers (#13), else exponential backoff."""
    for header in ("Retry-After", "RateLimit-Reset"):
        value = get_header(resp.headers, header)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return _BACKOFF_BASE * (2 ** (attempt - 1))


def send(record, config, token_provider, logger, http_post=_default_http_post, sleep=time.sleep) -> SendOutcome:
    """Send one record to ``POST {base_url}/ingest`` and classify the outcome."""
    # Client-side size guard — mirror the server's 1 MB cap before sending.
    if record.size > config.max_bytes:
        logger.info("skip %s: %d bytes exceeds max_bytes %d",
                    record.slug, record.size, config.max_bytes)
        return SendOutcome(result=ledger.RESULT_TOO_LARGE)

    with open(record.path, "rb") as f:
        body = f.read()

    url = f"{config.base_url}/ingest"
    headers = {
        "Authorization": "Bearer " + token_provider.get_token(),
        "Content-Type": "text/markdown",
        "X-Gbrain-Slug": record.slug,
        "X-Gbrain-Source-Id": record.source,
        "X-Gbrain-Source-Uri": f"file://{record.rel_path}",
    }

    refreshed = False
    backoff_attempts = 0
    start = time.time()

    while True:
        resp = http_post(url, body, headers)
        status = resp.status
        latency_ms = int((time.time() - start) * 1000)

        if status == 202:
            job_id, server_hash = _parse_accepted(resp)
            logger.info("sent %s source=%s status=202 job_id=%s bytes=%d latency_ms=%d",
                        record.slug, record.source, job_id, record.size, latency_ms)
            return SendOutcome(result=ledger.RESULT_SENT, http_status=202,
                               job_id=job_id, server_content_hash=server_hash)

        if status == 401:
            if refreshed:
                logger.info("error %s source=%s status=401 (re-auth failed)",
                            record.slug, record.source)
                return SendOutcome(result=ledger.RESULT_ERROR, http_status=401,
                                   error="authentication failed after token refresh")
            refreshed = True
            headers["Authorization"] = "Bearer " + token_provider.refresh()
            continue

        if status == 413:
            logger.info("too_large %s source=%s status=413", record.slug, record.source)
            return SendOutcome(result=ledger.RESULT_TOO_LARGE, http_status=413)

        if status == 403:
            logger.info("error %s source=%s status=403", record.slug, record.source)
            return SendOutcome(result=ledger.RESULT_ERROR, http_status=403, error=_SCOPE_HINT)

        if status in (400, 415):
            msg = _error_message(resp, status)
            logger.info("error %s source=%s status=%d", record.slug, record.source, status)
            return SendOutcome(result=ledger.RESULT_ERROR, http_status=status, error=msg)

        if status == 429 or status >= 500:
            backoff_attempts += 1
            if backoff_attempts >= _MAX_BACKOFF_ATTEMPTS:
                logger.info("error %s source=%s status=%d (retries exhausted)",
                            record.slug, record.source, status)
                return SendOutcome(result=ledger.RESULT_ERROR, http_status=status,
                                   error=f"retries exhausted after HTTP {status}")
            delay = _backoff_seconds(resp, backoff_attempts)
            logger.info("retry %s source=%s status=%d backoff=%.2fs",
                        record.slug, record.source, status, delay)
            sleep(delay)
            continue

        # Unexpected status — treat as a non-retryable error.
        logger.info("error %s source=%s status=%d (unexpected)",
                    record.slug, record.source, status)
        return SendOutcome(result=ledger.RESULT_ERROR, http_status=status,
                           error=f"unexpected HTTP {status}")


def _parse_accepted(resp):
    try:
        payload = json.loads(resp.body.decode("utf-8"))
        return payload.get("job_id"), payload.get("content_hash")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, None


def _error_message(resp, status: int) -> str:
    try:
        payload = json.loads(resp.body.decode("utf-8"))
        return payload.get("message") or payload.get("error") or f"HTTP {status}"
    except (json.JSONDecodeError, UnicodeDecodeError):
        return f"HTTP {status}"
