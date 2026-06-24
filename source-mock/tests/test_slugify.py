"""Matrix 1 — slugify(title) -> str (pure)."""
import unittest

from ingest.scanner import slugify


class TestSlugify(unittest.TestCase):
    # Matrix 1: slugify
    def test_cases(self):
        cases = [
            ("simple", "Weekly Sync", "weekly-sync"),
            ("punctuation", "Q3 Planning (draft!)", "q3-planning-draft"),
            ("underscores", "deal_notes_v2", "deal-notes-v2"),
            ("acronym", "OKR Review", "okr-review"),
            ("repeated-dashes", "a  --  b", "a-b"),
            ("trim", "  Hello!  ", "hello"),
            ("already-slug", "weekly-sync", "weekly-sync"),
            ("leading-digits", "2026 Kickoff", "2026-kickoff"),
            ("non-ascii", "Café Q&A", "caf-q-a"),
            ("all-stripped", "!!!", ""),
        ]
        for name, value, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(slugify(value), expected)


if __name__ == "__main__":
    unittest.main()
