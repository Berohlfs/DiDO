"""Append-only JSONL ledger, change detection, and the single-run lockfile."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime

log = logging.getLogger("ingest.ledger")

# Result enum (#9). `sent | too_large | error` are produced by sender.send;
# `skipped_unchanged | skipped_invalid` are produced by cli.
RESULT_SENT = "sent"
RESULT_SKIPPED_UNCHANGED = "skipped_unchanged"
RESULT_SKIPPED_INVALID = "skipped_invalid"
RESULT_TOO_LARGE = "too_large"
RESULT_ERROR = "error"


class LockHeld(Exception):
    """Raised when another ingest run already holds the lockfile."""


def load_index(path: str) -> dict:
    """Return ``{rel_path: last_entry}`` (last write wins). Missing/empty → {}."""
    index: dict = {}
    if not os.path.isfile(path):
        return index
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Tolerate a half-written/corrupt line and keep parsing.
                continue
            rel_path = entry.get("rel_path")
            if rel_path:
                index[rel_path] = entry
    return index


def needs_send(record, index: dict, force: bool) -> bool:
    """True if ``force``, the path is new, or the content hash changed."""
    if force:
        return True
    prev = index.get(record.rel_path)
    if prev is None:
        return True
    return prev.get("content_hash") != record.content_hash


def build_entry(*, record, result, timestamp: datetime, http_status=None,
                job_id=None, server_content_hash=None, error=None) -> dict:
    """Build one ledger row for a processed record."""
    return {
        "timestamp": timestamp.isoformat(),
        "rel_path": record.rel_path,
        "source": record.source,
        "slug": record.slug,
        "content_hash": record.content_hash,
        "bytes": record.size,
        "result": result,
        "http_status": http_status,
        "job_id": job_id,
        "server_content_hash": server_content_hash,
        "error": error,
    }


def append(path: str, entry: dict) -> None:
    """Append one JSON line, flushed per write so a crash never loses a send."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()
        os.fsync(f.fileno())


def acquire_lock(lock_path: str) -> int:
    """Acquire an exclusive lock via O_CREAT|O_EXCL. Raises LockHeld if taken."""
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise LockHeld(
            f"another ingest run is in progress (lock held at {lock_path}); "
            "if no run is active, delete the stale lockfile"
        )
    os.write(fd, str(os.getpid()).encode())
    return fd


def release_lock(fd: int, lock_path: str) -> None:
    """Release a previously-acquired lock; best effort."""
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.unlink(lock_path)
    except OSError:
        pass
