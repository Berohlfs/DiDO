"""argparse entrypoint: orchestration, summary output, exit codes."""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from . import auth, config as config_mod, ledger, scanner, sender


@dataclass
class Deps:
    """Injectable seams so the orchestration is testable without real I/O."""
    load_config: Callable = config_mod.load_config
    scan: Callable = scanner.scan
    resolve_explicit: Callable = scanner.resolve_explicit
    make_token_provider: Callable = field(default=lambda cfg: auth.TokenProvider(cfg))
    send: Callable = sender.send
    now: Callable = datetime.now


def _empty_summary() -> dict:
    return {
        "sent": 0,
        "skipped_unchanged": 0,
        "skipped_invalid": 0,
        "too_large": 0,
        "error": 0,
        "would_send": 0,
    }


def _parse_args(argv):
    p = argparse.ArgumentParser(
        prog="ingest",
        description="Push source markdown files to GBrain's POST /ingest webhook.",
    )
    p.add_argument("files", nargs="*",
                   help="explicit file paths to force-send (bypasses the ledger). "
                        "Omit to scan the full sources tree.")
    p.add_argument("--source", help="only scan this source subdir (e.g. fellow)")
    p.add_argument("--force", action="store_true",
                   help="resend every matched file, ignoring the ledger")
    p.add_argument("--dry-run", action="store_true",
                   help="scan and report; makes no HTTP calls and writes no ledger rows")
    p.add_argument("--config", default=".env", help="path to the .env config file")
    p.add_argument("--verbose", action="store_true", help="echo the run log to stderr")
    return p.parse_args(argv)


def _setup_logger(log_dir: str, now: datetime, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("ingest.run")
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    log_path = os.path.join(log_dir, f"run-{now.strftime('%Y%m%dT%H%M%S')}.log")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    if verbose:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    return logger, log_path


def run(argv=None, *, deps: Deps | None = None, return_summary: bool = False):
    """Run the ingest CLI. Returns an exit code (or ``(code, summary)``)."""
    deps = deps or Deps()
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    summary = _empty_summary()

    def ret(code):
        return (code, summary) if return_summary else code

    # --- config (exit 2 on failure) ---
    try:
        config = deps.load_config(args.config)
    except config_mod.ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return ret(2)

    sources_dir = config.sources_dir

    # #12: missing sources/ and no explicit files → nothing to do, exit 0.
    if not args.files and not os.path.isdir(sources_dir):
        print(f"sources directory {sources_dir!r} does not exist; nothing to do.")
        return ret(0)

    # --- lockfile (exit 2 if held) ---
    os.makedirs(config.log_dir, exist_ok=True)
    lock_path = os.path.join(config.log_dir, ".lock")
    try:
        lock_fd = ledger.acquire_lock(lock_path)
    except ledger.LockHeld as e:
        print(f"{e}", file=sys.stderr)
        return ret(2)

    try:
        logger, log_path = _setup_logger(config.log_dir, deps.now(), args.verbose)

        # --- resolve the work-list ---
        explicit_mode = bool(args.files)
        if explicit_mode:
            records = []
            for f in args.files:
                try:
                    records.append(deps.resolve_explicit(f, sources_dir))
                except ValueError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return ret(2)
        else:
            scan_result = deps.scan(sources_dir, only_source=args.source)
            records = scan_result.records
            summary["skipped_invalid"] = len(scan_result.skipped)

        ledger_path = os.path.join(config.log_dir, "ledger.jsonl")
        index = ledger.load_index(ledger_path)
        force_flag = args.force or explicit_mode

        to_send = [r for r in records if ledger.needs_send(r, index, force_flag)]
        unchanged = [r for r in records if r not in to_send]
        summary["skipped_unchanged"] = len(unchanged)

        # --- dry-run: report only, no HTTP, no ledger (#2) ---
        if args.dry_run:
            summary["would_send"] = len(to_send)
            for r in to_send:
                print(f"would send  {r.slug}  ({r.size} bytes)")
            _print_summary(summary, log_path, dry_run=True)
            return ret(0)

        # --- mint token eagerly so auth failure is a clean exit 2 ---
        token_provider = deps.make_token_provider(config)
        if to_send:
            try:
                token_provider.get_token()
            except auth.TokenError as e:
                print(f"auth error: {e}", file=sys.stderr)
                return ret(2)

        now = deps.now()
        for r in to_send:
            outcome = deps.send(r, config, token_provider, logger)
            summary[outcome.result] = summary.get(outcome.result, 0) + 1
            ledger.append(ledger_path, ledger.build_entry(
                record=r,
                result=outcome.result,
                timestamp=now,
                http_status=outcome.http_status,
                job_id=outcome.job_id,
                server_content_hash=outcome.server_content_hash,
                error=outcome.error,
            ))

        _print_summary(summary, log_path, dry_run=False)
        return ret(1 if summary["error"] else 0)
    finally:
        ledger.release_lock(lock_fd, lock_path)


def _print_summary(summary: dict, log_path: str, dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    if dry_run:
        print(f"{prefix}would send: {summary['would_send']}  "
              f"skipped_unchanged: {summary['skipped_unchanged']}  "
              f"skipped_invalid: {summary['skipped_invalid']}")
    else:
        print(f"sent: {summary['sent']}  "
              f"skipped_unchanged: {summary['skipped_unchanged']}  "
              f"skipped_invalid: {summary['skipped_invalid']}  "
              f"too_large: {summary['too_large']}  "
              f"error: {summary['error']}")
    print(f"log: {log_path}")


def main(argv=None) -> int:
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
