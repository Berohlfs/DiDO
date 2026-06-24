# `ingest` — push source files to GBrain's `/ingest` webhook

A small, stdlib-only Python CLI that scans clean markdown files and uploads
new/changed ones to a running [gbrain](../gbrain) server's `POST /ingest`
endpoint. One file in → one brain page out. It is a dumb-but-reliable uploader:
no transform, no enrichment, no embedding (embedding is the server's job).

Run everything from inside this `source-mock/` directory.

## Requirements

- Python 3.9+ (stdlib only — no `pip install`, no virtualenv needed).
- A reachable gbrain HTTP server and a `client_credentials` OAuth client with
  the **`write`** scope.

## Credential setup

On the gbrain host, register a client **with the `write` scope** and copy the
IDs into `.env`:

```sh
gbrain auth register-client dido-ingest \
    --grant-types client_credentials \
    --scopes "read write"
```

> The bare `register-client` defaults to `read` only, and `POST /ingest`
> requires `write` — a read-only token returns **403**. Always pass
> `--scopes "read write"`.

Then:

```sh
cp .env.example .env   # fill in GBRAIN_BASE_URL / CLIENT_ID / CLIENT_SECRET
```

### `.env` keys

| Key | Required | Default | Meaning |
|---|---|---|---|
| `GBRAIN_BASE_URL` | yes | — | gbrain server base URL |
| `GBRAIN_CLIENT_ID` | yes | — | OAuth client id |
| `GBRAIN_CLIENT_SECRET` | yes | — | OAuth client secret |
| `GBRAIN_SCOPES` | no | `read write` | scopes requested at mint (needs `write`) |
| `GBRAIN_SOURCES_DIR` | no | `sources` | input root |
| `GBRAIN_LOG_DIR` | no | `.ingest-logs` | ledger + run logs (gitignored) |
| `GBRAIN_MAX_BYTES` | no | `1048576` | client-side size cap (mirrors server) |

Real environment variables override `.env`. Secrets and bearer tokens are
**never** written to the run logs.

## Directory layout & slug rule

Files live at a **fixed depth**:

```
sources/<source>/<YYYY-MM-DD>/<Title>.md
```

- The **date** comes from the directory, the **title** from the filename stem.
- The destination page **slug** is `<source>/<date>-<slugified-title>`, e.g.
  `sources/fellow/2026-06-20/Weekly Sync.md` → `fellow/2026-06-20-weekly-sync`.
- Slugify: lowercase, every run of non-`[a-z0-9]` → `-`, trim. So
  `"Q3 Planning (draft!)"` → `q3-planning-draft`.

The slug is **stable across content edits**, so re-ingesting an edited file
updates the same page rather than creating a new one.

### Files that are skipped (with a warning)

- Files not inside a valid `YYYY-MM-DD` directory, malformed date dirs,
  non-`.md` files, or anything nested deeper than the fixed depth.
- **Non-UTF-8** files — the server would lossily decode them to `U+FFFD` and
  silently garble the page, so they are refused client-side.
- Titles that slugify to empty (e.g. `!!!.md`).
- **Slug collisions** — if two titles in one `source/date` collapse to the same
  slug (e.g. `Q3 Planning.md` + `q3 planning!!.md`), **every** member is skipped
  so nothing is silently clobbered server-side. Rename to disambiguate.

## Usage

```sh
python -m ingest                 # scan + send new/changed files
python -m ingest --dry-run       # report would-send set; no HTTP, no ledger write
python -m ingest --force         # resend every matched file, ignoring the ledger
python -m ingest --source fellow # only scan the fellow/ source
python -m ingest path/to/file.md # force-send explicit files (ledger bypassed)
python -m ingest --config .env --verbose
```

## State: the ledger vs. server dedup

- Locally, the CLI keeps an append-only JSONL **ledger** at
  `.ingest-logs/ledger.jsonl`, keyed by file path + content hash. By default it
  only sends files that are new or whose content changed; `--force` overrides
  this.
- Independently, the **server** dedups on `(client_id, content_hash)`: re-sending
  identical content returns the same job and creates no duplicate page. So even a
  forced re-send of unchanged content is a no-op server-side.

The two layers are complementary — the ledger avoids needless requests; the
server guarantees idempotency.

## Caveats

- **Renames orphan the old page.** The ledger is path-keyed, so renaming a file
  creates a new page under the new slug and leaves the old page behind (v1 does
  no orphan cleanup).
- **Files > 1 MB are skipped** (`too_large`), not chunked.
- **Single run at a time.** A lockfile at `.ingest-logs/.lock` prevents
  concurrent runs (which could double-send or read a half-written ledger). A
  second run exits with code 2. If a run is killed uncleanly, delete the stale
  `.lock` file.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | clean — every file sent or skipped, zero errors |
| `1` | partial failure — at least one `error` result (exhausted retries / 400 / 415 / 403) |
| `2` | startup failure — missing/invalid config, token-mint failure, or lock held |

## Tests

```sh
python -m unittest discover -s tests
```

Matrix-driven stdlib `unittest`, no third-party dependencies, no real network.
