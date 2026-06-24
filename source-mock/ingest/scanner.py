"""Walk the fixed-depth source tree, validate, and derive ingest records.

Layout (fixed depth): ``sources/<source>/<YYYY-MM-DD>/<Title>.md``.
The date comes from the directory, the title from the filename stem.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

log = logging.getLogger("ingest.scanner")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Lowercase, collapse every run of non-``[a-z0-9]`` to ``-``, trim ``-``.

    ``"Q3 Planning (draft!)"`` -> ``"q3-planning-draft"``. An all-stripped
    title (e.g. ``"!!!"``) yields ``""`` — the caller treats that as invalid.
    """
    return _SLUG_STRIP_RE.sub("-", title.lower()).strip("-")


@dataclass
class FileRecord:
    rel_path: str          # path relative to sources_dir, the ledger key
    source: str
    date: str
    title: str
    slug: str
    content_hash: str      # sha256 hex over the raw bytes
    size: int
    path: str              # absolute path to read the body from


@dataclass
class SkippedFile:
    rel_path: str
    reason: str            # no_date_dir | bad_date | not_md | too_deep |
                           # empty_slug | slug_collision | non_utf8


@dataclass
class ScanResult:
    records: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _read_record(source: str, date: str, filename: str, abs_path: str):
    """Build a FileRecord or return a SkippedFile reason string.

    Returns ``(FileRecord, None)`` on success or ``(None, reason)`` on a gate
    failure (non-UTF-8 body or empty slug).
    """
    with open(abs_path, "rb") as f:
        raw = f.read()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        # The server lossily decodes invalid bytes to U+FFFD (it does NOT
        # 400), which would silently garble the page — refuse client-side.
        return None, "non_utf8"
    title = filename[:-3]  # strip ".md"
    slug_title = slugify(title)
    if not slug_title:
        return None, "empty_slug"
    rec = FileRecord(
        rel_path=f"{source}/{date}/{filename}",
        source=source,
        date=date,
        title=title,
        slug=f"{source}/{date}-{slug_title}",
        content_hash=hashlib.sha256(raw).hexdigest(),
        size=len(raw),
        path=abs_path,
    )
    return rec, None


def scan(sources_dir: str, only_source: str | None = None) -> ScanResult:
    """Scan ``sources_dir`` for valid markdown pages at the fixed depth."""
    result = ScanResult()
    if not os.path.isdir(sources_dir):
        log.warning("sources directory %r does not exist; nothing to scan", sources_dir)
        return result

    provisional: list[FileRecord] = []

    for source in sorted(os.listdir(sources_dir)):
        source_path = os.path.join(sources_dir, source)
        if not os.path.isdir(source_path):
            continue
        if only_source is not None and source != only_source:
            continue

        for entry in sorted(os.listdir(source_path)):
            entry_path = os.path.join(source_path, entry)
            if os.path.isfile(entry_path):
                # A loose file directly under the source dir (no date dir).
                rel = f"{source}/{entry}"
                log.warning("skip %s: file is not inside a YYYY-MM-DD date dir", rel)
                result.skipped.append(SkippedFile(rel, "no_date_dir"))
                continue
            if not _DATE_RE.match(entry):
                rel = f"{source}/{entry}"
                log.warning("skip %s: directory name is not a valid YYYY-MM-DD date", rel)
                result.skipped.append(SkippedFile(rel, "bad_date"))
                continue

            date = entry
            for fname in sorted(os.listdir(entry_path)):
                fpath = os.path.join(entry_path, fname)
                rel = f"{source}/{date}/{fname}"
                if os.path.isdir(fpath):
                    # Deeper nesting than the fixed depth — skip the subtree.
                    log.warning("skip %s/: nested deeper than the fixed layout depth", rel)
                    result.skipped.append(SkippedFile(rel, "too_deep"))
                    continue
                if not fname.endswith(".md"):
                    log.warning("skip %s: not a .md file", rel)
                    result.skipped.append(SkippedFile(rel, "not_md"))
                    continue
                rec, reason = _read_record(source, date, fname, fpath)
                if reason is not None:
                    log.warning("skip %s: %s", rel, reason)
                    result.skipped.append(SkippedFile(rel, reason))
                    continue
                provisional.append(rec)

    # Slug-collision detection: two distinct titles in one source/date can
    # collapse to the same slug, which would silently overwrite a page
    # server-side. Warn and skip every member of a colliding set.
    by_slug: dict[str, list[FileRecord]] = defaultdict(list)
    for rec in provisional:
        by_slug[rec.slug].append(rec)
    for slug, recs in by_slug.items():
        if len(recs) > 1:
            for rec in recs:
                log.warning("skip %s: slug %r collides with another file; rename to disambiguate",
                            rec.rel_path, slug)
                result.skipped.append(SkippedFile(rec.rel_path, "slug_collision"))
        else:
            result.records.append(recs[0])

    return result


def resolve_explicit(path: str, sources_dir: str) -> FileRecord:
    """Resolve an explicit CLI file path to a FileRecord (force-send, #10).

    The path must match the ``<source>/<date>/<title>.md`` layout. Anything
    else raises ``ValueError`` with a clear message.
    """
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        raise ValueError(f"{path}: not a file")
    if not abs_path.endswith(".md"):
        raise ValueError(f"{path}: not a .md file")

    sources_root = os.path.abspath(sources_dir)
    rel = os.path.relpath(abs_path, sources_root)
    parts = rel.split(os.sep)
    if len(parts) != 3 or parts[0] in ("", os.pardir):
        raise ValueError(
            f"{path}: does not match the sources/<source>/<YYYY-MM-DD>/<title>.md layout"
        )
    source, date, fname = parts
    if not _DATE_RE.match(date):
        raise ValueError(f"{path}: {date!r} is not a valid YYYY-MM-DD date directory")

    rec, reason = _read_record(source, date, fname, abs_path)
    if reason is not None:
        raise ValueError(f"{path}: {reason}")
    return rec
