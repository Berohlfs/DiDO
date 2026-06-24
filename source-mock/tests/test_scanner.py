"""Matrix 2 — scanner.scan(sources_dir, only_source=None) (temp tree)."""
import hashlib
import os
import tempfile
import unittest

from ingest import scanner


def write(root, rel, content=b"# hello\n"):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return path


def slugs(result):
    return sorted(r.slug for r in result.records)


def reasons(result):
    return sorted(s.reason for s in result.skipped)


class TestScanner(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.sources = os.path.join(self.root, "sources")
        os.makedirs(self.sources, exist_ok=True)

    def tearDown(self):
        self._tmp.cleanup()

    # Matrix 2: valid file → one record with correct slug/source/date/hash
    def test_valid_file(self):
        body = b"# Weekly Sync\n\nnotes\n"
        write(self.sources, "fellow/2026-06-20/Weekly Sync.md", body)
        res = scanner.scan(self.sources)
        self.assertEqual(len(res.records), 1)
        rec = res.records[0]
        self.assertEqual(rec.slug, "fellow/2026-06-20-weekly-sync")
        self.assertEqual(rec.source, "fellow")
        self.assertEqual(rec.date, "2026-06-20")
        self.assertEqual(rec.title, "Weekly Sync")
        self.assertEqual(rec.rel_path, "fellow/2026-06-20/Weekly Sync.md")
        self.assertEqual(rec.content_hash, hashlib.sha256(body).hexdigest())
        self.assertEqual(rec.size, len(body))

    # Matrix 2: loose file directly under source (no date dir) → skipped+warn
    def test_loose_file_no_date_dir(self):
        write(self.sources, "fellow/loose.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertTrue(res.skipped)

    # Matrix 2: unpadded date dir → skipped
    def test_unpadded_date(self):
        write(self.sources, "fellow/2026-6-20/x.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertTrue(res.skipped)

    # Matrix 2: non-date dir name → skipped
    def test_non_date_dir(self):
        write(self.sources, "fellow/June-20/x.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertTrue(res.skipped)

    # Matrix 2: non-.md under a valid date dir → skipped+warn
    def test_non_md_extension(self):
        write(self.sources, "fellow/2026-06-20/notes.txt")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertTrue(res.skipped)

    # Matrix 2: deeper nesting than fixed depth → skipped
    def test_deeper_nest(self):
        write(self.sources, "fellow/2026-06-20/sub/x.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertTrue(res.skipped)

    # Matrix 2: two sources present → both scanned
    def test_two_sources(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        write(self.sources, "cowork/2026-06-21/B.md")
        res = scanner.scan(self.sources)
        self.assertEqual(slugs(res), ["cowork/2026-06-21-b", "fellow/2026-06-20-a"])

    # Matrix 2: only_source filter
    def test_only_source(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        write(self.sources, "cowork/2026-06-21/B.md")
        res = scanner.scan(self.sources, only_source="cowork")
        self.assertEqual(slugs(res), ["cowork/2026-06-21-b"])

    # Matrix 2: title slugifying to empty → skipped_invalid+warn
    def test_empty_slug(self):
        write(self.sources, "fellow/2026-06-20/!!!.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertIn("empty_slug", reasons(res))

    # Matrix 2: two distinct titles, same date → two records
    def test_two_distinct_titles(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        write(self.sources, "fellow/2026-06-20/B.md")
        res = scanner.scan(self.sources)
        self.assertEqual(len(res.records), 2)

    # Matrix 2 (#3): slug collision → both skipped_invalid, none sent
    def test_slug_collision(self):
        write(self.sources, "fellow/2026-06-20/Q3 Planning.md")
        write(self.sources, "fellow/2026-06-20/q3 planning!!.md")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertIn("slug_collision", reasons(res))
        self.assertGreaterEqual(len(res.skipped), 2)

    # Matrix 2 (#5): non-UTF-8 file → skipped_invalid+warn
    def test_non_utf8(self):
        write(self.sources, "fellow/2026-06-20/bad.md", b"\xff\xfe\x00bad")
        res = scanner.scan(self.sources)
        self.assertEqual(res.records, [])
        self.assertIn("non_utf8", reasons(res))

    # Matrix 2: content_hash over raw bytes — identical bytes → identical hash
    def test_hash_over_raw_bytes(self):
        body = b"identical bytes here"
        write(self.sources, "fellow/2026-06-20/A.md", body)
        write(self.sources, "cowork/2026-06-20/B.md", body)
        res = scanner.scan(self.sources)
        hashes = {r.content_hash for r in res.records}
        self.assertEqual(len(hashes), 1)

    # Matrix 2 (#12): missing sources_dir → empty result + warn, no raise
    def test_missing_sources_dir(self):
        res = scanner.scan(os.path.join(self.root, "does-not-exist"))
        self.assertEqual(res.records, [])
        self.assertEqual(res.skipped, [])


class TestResolveExplicit(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.sources = os.path.join(self.root, "sources")
        os.makedirs(self.sources, exist_ok=True)

    def tearDown(self):
        self._tmp.cleanup()

    # Matrix 2 (#10): explicit path resolves to a FileRecord
    def test_resolve_valid(self):
        p = write(self.sources, "fellow/2026-06-20/Weekly Sync.md", b"x")
        rec = scanner.resolve_explicit(p, self.sources)
        self.assertEqual(rec.slug, "fellow/2026-06-20-weekly-sync")
        self.assertEqual(rec.rel_path, "fellow/2026-06-20/Weekly Sync.md")

    # Matrix 2 (#10): explicit path not matching layout → clear error
    def test_resolve_bad_layout(self):
        p = write(self.sources, "fellow/loose.md", b"x")
        with self.assertRaises(ValueError):
            scanner.resolve_explicit(p, self.sources)


if __name__ == "__main__":
    unittest.main()
