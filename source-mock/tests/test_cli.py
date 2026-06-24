"""Matrix 7 — cli orchestration (integration, all fakes)."""
import os
import tempfile
import unittest
from datetime import datetime

from ingest import cli, ledger, scanner
from ingest.config import Config, ConfigError
from ingest.sender import SendOutcome


def write(root, rel, content=b"# hi\n"):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return path


class FakeTokenProvider:
    def get_token(self):
        return "tok"

    def refresh(self):
        return "tok"


class FakeSender:
    """Records each send; returns a configurable result per slug (default sent)."""

    def __init__(self, results=None):
        self.results = results or {}
        self.sent = []

    def __call__(self, record, config, token_provider, logger):
        self.sent.append(record.slug)
        result = self.results.get(record.slug, ledger.RESULT_SENT)
        if result == ledger.RESULT_SENT:
            return SendOutcome(result=result, http_status=202, job_id="job-" + record.slug)
        if result == ledger.RESULT_TOO_LARGE:
            return SendOutcome(result=result, http_status=413)
        return SendOutcome(result=result, http_status=500, error="boom")


class CliTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.sources = os.path.join(self.root, "sources")
        self.logs = os.path.join(self.root, ".ingest-logs")
        os.makedirs(self.sources, exist_ok=True)
        self.config = Config(
            base_url="http://x",
            client_id="id",
            client_secret="sec",
            scopes="read write",
            sources_dir=self.sources,
            log_dir=self.logs,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def deps(self, sender, *, load_config=None):
        return cli.Deps(
            load_config=load_config or (lambda path: self.config),
            scan=scanner.scan,
            resolve_explicit=scanner.resolve_explicit,
            make_token_provider=lambda cfg: FakeTokenProvider(),
            send=sender,
            now=lambda: datetime(2026, 6, 20, 9, 0, 0),
        )

    def run_cli(self, argv, sender, **kw):
        return cli.run(argv, deps=self.deps(sender, **kw))

    def ledger_path(self):
        return os.path.join(self.logs, "ledger.jsonl")


class TestCli(CliTestBase):
    # Matrix 7: mixed tree → correct summary counts and exit 0 when clean
    def test_mixed_counts(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        write(self.sources, "fellow/2026-06-20/B.md")
        write(self.sources, "fellow/2026-06-20/!!!.md")  # skipped_invalid (empty slug)
        sender = FakeSender()
        code, summary = cli.run(["--config", ".env"], deps=self.deps(sender), return_summary=True)
        self.assertEqual(code, 0)
        self.assertEqual(summary["sent"], 2)
        self.assertEqual(summary["skipped_invalid"], 1)
        self.assertEqual(summary["error"], 0)

    # Matrix 7: any error result → exit 1
    def test_error_exit_1(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        sender = FakeSender(results={"fellow/2026-06-20-a": ledger.RESULT_ERROR})
        code, summary = cli.run([], deps=self.deps(sender), return_summary=True)
        self.assertEqual(code, 1)
        self.assertEqual(summary["error"], 1)

    # Matrix 7: too_large counted, still exit 0 (not an error)
    def test_too_large_counted(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        sender = FakeSender(results={"fellow/2026-06-20-a": ledger.RESULT_TOO_LARGE})
        code, summary = cli.run([], deps=self.deps(sender), return_summary=True)
        self.assertEqual(code, 0)
        self.assertEqual(summary["too_large"], 1)

    # Matrix 7 (#2): --dry-run → zero sends and zero ledger rows
    def test_dry_run_no_send_no_ledger(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        sender = FakeSender()
        code, summary = cli.run(["--dry-run"], deps=self.deps(sender), return_summary=True)
        self.assertEqual(code, 0)
        self.assertEqual(sender.sent, [])
        self.assertFalse(os.path.exists(self.ledger_path()))
        # still reports the would-send set
        self.assertEqual(summary["would_send"], 1)

    # Matrix 7: second run skips unchanged via ledger
    def test_skips_unchanged_on_second_run(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        cli.run([], deps=self.deps(FakeSender()))
        sender2 = FakeSender()
        code, summary = cli.run([], deps=self.deps(sender2), return_summary=True)
        self.assertEqual(sender2.sent, [])
        self.assertEqual(summary["skipped_unchanged"], 1)

    # Matrix 7: --force re-sends ledger-unchanged files
    def test_force_resends(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        cli.run([], deps=self.deps(FakeSender()))
        sender2 = FakeSender()
        cli.run(["--force"], deps=self.deps(sender2))
        self.assertEqual(sender2.sent, ["fellow/2026-06-20-a"])

    # Matrix 7: --source filters
    def test_source_filter(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        write(self.sources, "cowork/2026-06-21/B.md")
        sender = FakeSender()
        cli.run(["--source", "cowork"], deps=self.deps(sender))
        self.assertEqual(sender.sent, ["cowork/2026-06-21-b"])

    # Matrix 7 (#10): explicit file args are force-sent regardless of ledger
    def test_explicit_files_force_sent(self):
        p = write(self.sources, "fellow/2026-06-20/A.md")
        cli.run([], deps=self.deps(FakeSender()))  # establishes ledger entry
        sender2 = FakeSender()
        cli.run([p], deps=self.deps(sender2))
        self.assertEqual(sender2.sent, ["fellow/2026-06-20-a"])

    # Matrix 7: ledger rows appended per attempt (non-dry-run)
    def test_ledger_appended(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        cli.run([], deps=self.deps(FakeSender()))
        index = ledger.load_index(self.ledger_path())
        self.assertIn("fellow/2026-06-20/A.md", index)

    # Matrix 7: missing config → exit 2
    def test_missing_config_exit_2(self):
        def bad_load(path):
            raise ConfigError("missing base_url")
        code = cli.run([], deps=self.deps(FakeSender(), load_config=bad_load))
        self.assertEqual(code, 2)

    # Matrix 7 (#12): missing sources/ with no explicit files → warn + exit 0
    def test_missing_sources_exit_0(self):
        self.config.sources_dir = os.path.join(self.root, "nope")
        sender = FakeSender()
        code = cli.run([], deps=self.deps(sender))
        self.assertEqual(code, 0)
        self.assertEqual(sender.sent, [])

    # Matrix 7 (#6): second invocation while .lock exists → exit 2, no send
    def test_lock_held_exit_2(self):
        write(self.sources, "fellow/2026-06-20/A.md")
        os.makedirs(self.logs, exist_ok=True)
        fd = ledger.acquire_lock(os.path.join(self.logs, ".lock"))
        try:
            sender = FakeSender()
            code = cli.run([], deps=self.deps(sender))
            self.assertEqual(code, 2)
            self.assertEqual(sender.sent, [])
        finally:
            ledger.release_lock(fd, os.path.join(self.logs, ".lock"))


if __name__ == "__main__":
    unittest.main()
