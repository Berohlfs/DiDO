"""Matrix 5 — sender.send(record, config, token_provider, http_post, sleep) (fake transport)."""
import json
import logging
import os
import tempfile
import unittest

from ingest import sender, ledger
from ingest.config import Config
from ingest.scanner import FileRecord
from ingest.transport import HttpResponse


SECRET = "cs_super_secret_value"
BEARER = "bearer-token-xyz"


def cfg(max_bytes=1_048_576):
    return Config(
        base_url="http://localhost:8787",
        client_id="cl_id",
        client_secret=SECRET,
        scopes="read write",
        max_bytes=max_bytes,
    )


class FakeTokenProvider:
    def __init__(self, token=BEARER):
        self.token = token
        self.refresh_calls = 0

    def get_token(self):
        return self.token

    def refresh(self):
        self.refresh_calls += 1
        return self.token


class FakeTransport:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, url, data, headers):
        self.calls.append({"url": url, "data": data, "headers": headers})
        return self._responses.pop(0)


def accepted(job_id="job-1", content_hash="abc"):
    body = json.dumps({
        "job_id": job_id,
        "content_hash": content_hash,
        "source_id": "fellow",
        "message": "Accepted.",
    }).encode()
    return HttpResponse(202, {"content-type": "application/json"}, body)


def status(code, headers=None, body=b"{}"):
    return HttpResponse(code, headers or {}, body)


class SenderTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.body = b"# Weekly Sync\n\nbody bytes\n"
        path = os.path.join(self._tmp.name, "A.md")
        with open(path, "wb") as f:
            f.write(self.body)
        self.record = FileRecord(
            rel_path="fellow/2026-06-20/Weekly Sync.md",
            source="fellow",
            date="2026-06-20",
            title="Weekly Sync",
            slug="fellow/2026-06-20-weekly-sync",
            content_hash="hash",
            size=len(self.body),
            path=path,
        )
        self.logger = logging.getLogger("test.sender")
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)
        self.sleeps = []

    def tearDown(self):
        self._tmp.cleanup()

    def sleep(self, secs):
        self.sleeps.append(secs)

    def send(self, transport):
        return sender.send(
            self.record, cfg(), FakeTokenProvider(), self.logger,
            http_post=transport, sleep=self.sleep,
        )


class TestSender(SenderTestBase):
    # Matrix 5: 202 → sent, job_id parsed
    def test_202_sent(self):
        fake = FakeTransport([accepted(job_id="job-42")])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_SENT)
        self.assertEqual(out.job_id, "job-42")
        self.assertEqual(out.http_status, 202)

    # Matrix 5: header + body assertions
    def test_request_headers_and_body(self):
        fake = FakeTransport([accepted()])
        self.send(fake)
        call = fake.calls[0]
        self.assertEqual(call["url"], "http://localhost:8787/ingest")
        h = {k.lower(): v for k, v in call["headers"].items()}
        self.assertEqual(h["authorization"], "Bearer " + BEARER)
        self.assertEqual(h["content-type"], "text/markdown")
        self.assertEqual(h["x-gbrain-slug"], "fellow/2026-06-20-weekly-sync")
        self.assertEqual(h["x-gbrain-source-id"], "fellow")
        self.assertEqual(h["x-gbrain-source-uri"], "file://fellow/2026-06-20/Weekly Sync.md")
        self.assertEqual(call["data"], self.body)

    # Matrix 5: size > max_bytes → too_large, no HTTP call
    def test_too_large_no_call(self):
        fake = FakeTransport([])
        out = sender.send(
            self.record, cfg(max_bytes=5), FakeTokenProvider(), self.logger,
            http_post=fake, sleep=self.sleep,
        )
        self.assertEqual(out.result, ledger.RESULT_TOO_LARGE)
        self.assertEqual(fake.calls, [])

    # Matrix 5: 413 → too_large
    def test_413_too_large(self):
        fake = FakeTransport([status(413)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_TOO_LARGE)

    # Matrix 5: 401 → refresh() → 202 → sent (refresh invoked once)
    def test_401_then_sent(self):
        fake = FakeTransport([status(401), accepted()])
        tp = FakeTokenProvider()
        out = sender.send(self.record, cfg(), tp, self.logger, http_post=fake, sleep=self.sleep)
        self.assertEqual(out.result, ledger.RESULT_SENT)
        self.assertEqual(tp.refresh_calls, 1)

    # Matrix 5: 401 twice → error
    def test_401_twice_error(self):
        fake = FakeTransport([status(401), status(401)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_ERROR)

    # Matrix 5: 429 → 202 → sent (retry w/ backoff, sleep stubbed)
    def test_429_then_sent(self):
        fake = FakeTransport([status(429), accepted()])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_SENT)
        self.assertTrue(self.sleeps)

    # Matrix 5: 5xx → 202 → sent
    def test_5xx_then_sent(self):
        fake = FakeTransport([status(503), accepted()])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_SENT)

    # Matrix 5: 5xx exhausted → error
    def test_5xx_exhausted_error(self):
        fake = FakeTransport([status(500), status(500), status(500)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_ERROR)

    # Matrix 5: 400 → error, no retry (single call)
    def test_400_error_no_retry(self):
        fake = FakeTransport([status(400)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_ERROR)
        self.assertEqual(len(fake.calls), 1)

    # Matrix 5: 415 → error, no retry
    def test_415_error_no_retry(self):
        fake = FakeTransport([status(415)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_ERROR)
        self.assertEqual(len(fake.calls), 1)

    # Matrix 5 (#4): 403 → error, no retry, hint mentions --scopes "read write"
    def test_403_error_with_hint(self):
        fake = FakeTransport([status(403)])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_ERROR)
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("write", out.error)
        self.assertIn("scope", out.error.lower())

    # Matrix 5 (#13): 429 with Retry-After → sleep that value, not blind exponential
    def test_429_retry_after_header(self):
        fake = FakeTransport([status(429, headers={"Retry-After": "7"}), accepted()])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_SENT)
        self.assertIn(7.0, self.sleeps)

    # Matrix 5 (#13): 429 with RateLimit-Reset → sleep that value
    def test_429_ratelimit_reset_header(self):
        fake = FakeTransport([status(429, headers={"RateLimit-Reset": "4"}), accepted()])
        out = self.send(fake)
        self.assertEqual(out.result, ledger.RESULT_SENT)
        self.assertIn(4.0, self.sleeps)

    # Matrix 5 (#7): secret and bearer token never appear in the run log
    def test_secret_and_token_not_logged(self):
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        self.logger.addHandler(handler)
        fake = FakeTransport([accepted()])
        self.send(fake)
        handler.flush()
        out = stream.getvalue()
        self.assertNotIn(SECRET, out)
        self.assertNotIn(BEARER, out)


if __name__ == "__main__":
    unittest.main()
