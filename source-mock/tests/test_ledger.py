"""Matrix 4 — ledger (pure + temp file)."""
import json
import os
import tempfile
import unittest
from datetime import datetime

from ingest import ledger
from ingest.scanner import FileRecord


def make_record(rel_path="fellow/2026-06-20/A.md", content_hash="h1"):
    return FileRecord(
        rel_path=rel_path,
        source="fellow",
        date="2026-06-20",
        title="A",
        slug="fellow/2026-06-20-a",
        content_hash=content_hash,
        size=10,
        path="/abs/" + rel_path,
    )


class TestNeedsSend(unittest.TestCase):
    # Matrix 4: needs_send branches
    def test_new_path_true(self):
        self.assertTrue(ledger.needs_send(make_record(), {}, force=False))

    def test_changed_hash_true(self):
        index = {"fellow/2026-06-20/A.md": {"content_hash": "old"}}
        self.assertTrue(ledger.needs_send(make_record(content_hash="new"), index, force=False))

    def test_same_hash_false(self):
        index = {"fellow/2026-06-20/A.md": {"content_hash": "h1"}}
        self.assertFalse(ledger.needs_send(make_record(content_hash="h1"), index, force=False))

    def test_force_true(self):
        index = {"fellow/2026-06-20/A.md": {"content_hash": "h1"}}
        self.assertTrue(ledger.needs_send(make_record(content_hash="h1"), index, force=True))


class TestIndex(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "ledger.jsonl")

    def tearDown(self):
        self._tmp.cleanup()

    # Matrix 4: duplicate path → last write wins
    def test_duplicate_path_last_wins(self):
        with open(self.path, "w") as f:
            f.write(json.dumps({"rel_path": "a", "content_hash": "first"}) + "\n")
            f.write(json.dumps({"rel_path": "a", "content_hash": "second"}) + "\n")
        index = ledger.load_index(self.path)
        self.assertEqual(index["a"]["content_hash"], "second")

    # Matrix 4: missing/empty file → empty index
    def test_missing_file_empty(self):
        self.assertEqual(ledger.load_index(self.path), {})
        open(self.path, "w").close()
        self.assertEqual(ledger.load_index(self.path), {})

    # Matrix 4: append then reload round-trips
    def test_append_roundtrip(self):
        entry = ledger.build_entry(
            record=make_record(),
            result=ledger.RESULT_SENT,
            timestamp=datetime(2026, 6, 20, 12, 0, 0),
            http_status=202,
            job_id="job-1",
        )
        ledger.append(self.path, entry)
        index = ledger.load_index(self.path)
        self.assertIn("fellow/2026-06-20/A.md", index)
        self.assertEqual(index["fellow/2026-06-20/A.md"]["job_id"], "job-1")
        self.assertEqual(index["fellow/2026-06-20/A.md"]["result"], "sent")

    # Matrix 4: malformed JSON line → skipped, parsing continues
    def test_malformed_line_skipped(self):
        with open(self.path, "w") as f:
            f.write("not json at all\n")
            f.write(json.dumps({"rel_path": "b", "content_hash": "ok"}) + "\n")
        index = ledger.load_index(self.path)
        self.assertEqual(index["b"]["content_hash"], "ok")
        self.assertEqual(len(index), 1)


class TestLock(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lock = os.path.join(self._tmp.name, ".lock")

    def tearDown(self):
        self._tmp.cleanup()

    def test_acquire_then_second_raises(self):
        fd = ledger.acquire_lock(self.lock)
        try:
            with self.assertRaises(ledger.LockHeld):
                ledger.acquire_lock(self.lock)
        finally:
            ledger.release_lock(fd, self.lock)
        # released → can acquire again
        fd2 = ledger.acquire_lock(self.lock)
        ledger.release_lock(fd2, self.lock)


if __name__ == "__main__":
    unittest.main()
