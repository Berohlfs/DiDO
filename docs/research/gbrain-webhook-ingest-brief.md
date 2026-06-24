# Research Brief: GBrain Webhook Ingest — Transcripts & AI Session Conversations

**Date**: 2026-06-24
**Requirement**: Build a server that pushes (1) video-call transcripts and (2) AI working-session conversations into GBrain's webhook receivers.
**Verdict**: Ready for Planning — with one architectural decision to resolve (see Open Questions: Path A vs Path B).

---

## Scope

**In scope**
- Locate GBrain's actual webhook *receivers* in the `gbrain/` subrepo.
- Document the endpoint(s), auth, payload/content model, headers, response, and constraints for sending transcripts + AI-session conversations.
- Map what a sending server must do to interface effectively.

**Out of scope (for this brief)**
- Building the sending server itself (that's `/loop-plan`).
- The transcript *capture* side (Zoom/Meet/Circleback APIs) — only the GBrain-facing contract.
- Entity-propagation/enrichment logic (a GBrain agent-side concern, see Path B).
- Embedding/search tuning beyond noting when ingested content becomes searchable.

---

## Landscape

**Tech stack (gbrain subrepo)**: TypeScript on **Bun**; Express 5 HTTP server; `@modelcontextprotocol/sdk` for MCP + OAuth 2.1; storage engine is PGLite (default) or Postgres+pgvector. Minion job queue (`MinionQueue`) is the async work primitive.

**There are two native HTTP webhook receivers, both inside `gbrain serve --http`** (`gbrain/src/commands/serve-http.ts`):

| Endpoint | Purpose | Auth | Relevant? |
|---|---|---|---|
| `POST /ingest` | Generic content webhook → becomes a brain page | OAuth 2.1 bearer, `write` scope | **YES — this is the target** |
| `POST /webhooks/github` | Push-triggered `gbrain sync` of a git-backed source | HMAC `X-Hub-Signature-256` | No (repo-sync only) |

**A third, NON-gbrain pattern exists in the docs** and is easy to mistake for a gbrain receiver: `{your_agent_gateway}/hooks/circleback-meetings`, `/hooks/quo-events` (`gbrain/docs/integrations/meeting-webhooks.md`). These URLs live in the *user's own agent harness* (OpenClaw/Hermes), **not** in gbrain. The agent receives them, runs the `meeting-ingestion` / `webhook-transforms` skills, and writes to the brain via CLI/MCP. This is "Path B" below.

**Key files**
- `gbrain/src/commands/serve-http.ts:1724-1967` — `POST /ingest` handler (the contract).
- `gbrain/src/core/ingestion/types.ts` — `IngestionEvent` shape + `validateIngestionEvent` + content-type taxonomy.
- `gbrain/src/core/minions/handlers/ingest-capture.ts` — what happens after accept: slug resolution + `importFromContent` → brain page.
- `gbrain/src/commands/auth.ts` — `gbrain auth register-client` (mint OAuth client).
- `gbrain/src/core/scope.ts` — scope set (`read|write|admin|sources_admin|users_admin|agent`).
- `gbrain/test/e2e/serve-http-ingest-webhook.test.ts` — executable spec of every status-code branch.
- `gbrain/skills/webhook-transforms/SKILL.md`, `gbrain/skills/meeting-ingestion` + `docs/guides/meeting-ingestion.md` — Path B (agent-mediated) pattern.

---

## Patterns & Conventions

### The `POST /ingest` contract (the primary interface)

**Auth**: OAuth 2.1, `Authorization: Bearer <access_token>`, token must carry the **`write`** scope. Missing token → 401; token without `write` → 403.

**Getting a token (client_credentials flow):**
1. On the server hosting gbrain, register a client:
   `gbrain auth register-client <name> --grant-types client_credentials --scopes "read write"`
   → returns `Client ID: gbrain_cl_…` and `Client Secret: gbrain_cs_…` (secret stored hashed; shown once).
2. Exchange for a token:
   `POST /token` (form-urlencoded) `grant_type=client_credentials&client_id=…&client_secret=…&scope=read%20write` → `{ access_token, … }`.
   Tokens are TTL'd (sweep on startup); re-mint on expiry.

**Request**:
- Method/route: `POST /ingest`
- Body: **raw** (`express.raw`, parsed by bytes, not JSON) — the body *is* the page content.
- Content-Type allowlist: `text/markdown`, `text/plain`, `text/html`, `application/json`. Unknown `text/*` is coerced to `text/plain`. Binary (`image/*`, `audio/*`, `video/*`, `application/pdf`) → **415** (no processor in v1).
- Payload cap: **1 MB default**, server-tunable via `GBRAIN_INGEST_MAX_BYTES`.
- Rate limit: **100 requests / 10s per IP**.

**Optional control headers** (drive page identity/provenance):
| Header | Effect |
|---|---|
| `X-Gbrain-Content-Type` | Overrides request Content-Type (e.g. send body as octet-stream but declare `text/markdown`). |
| `X-Gbrain-Slug` | Sets the destination page slug (e.g. `meetings/2026-06-24-standup`). Else defaults to `inbox/YYYY-MM-DD-<hash6>`. |
| `X-Gbrain-Source-Id` | Tags the event's source instance (default `webhook-<clientId>`). |
| `X-Gbrain-Source-Uri` | Original URI/provenance (default `mcp-webhook:<clientId>:<ts>`). |

**Response**: `202 Accepted` → `{ job_id, content_hash, source_id, message }`. Errors are JSON envelopes: `empty_body` (400), `unsupported_content_type` (415), `invalid_event` (400), `queue_submission_failed`/`internal_error` (500).

**Idempotency**: queue dedup key is `ingest:webhook:<clientId>:<contentHash>`. Same content from same client → same `job_id` returned (no duplicate page). Per-client `maxWaiting: 50` cap.

### What happens after accept (`ingest_capture` handler)
- The handler routes the event through `importFromContent(engine, slug, content)` → lands one brain page.
- **Slug resolution order**: `X-Gbrain-Slug` (job.data.slug) → `metadata.slug` → default `inbox/YYYY-MM-DD-<hash6>`.
- **Content is stored as-authored.** v1 does **no** transform, no diarization formatting, no entity extraction, no timeline propagation, no auto-link. `untrusted_payload: true` is set on every webhook event and recorded for audit but **not yet enforced** at this layer.
- **Embeddings**: `noEmbed` defaults to `true` — the page imports but is **not embedded inline**. It becomes vector-searchable only after a separate embed pass (`gbrain embed --stale`, autopilot's embed phase, or `gbrain sync` for small changesets). One POST = one page.

### Path B — agent-mediated ingestion (the docs' recommended path for meetings)
`docs/guides/meeting-ingestion.md` + `skills/webhook-transforms` describe a richer flow where a webhook hits the *user's agent gateway*, and the agent: pulls the full diarized transcript, writes a "compiled truth" analysis above the bar + full transcript below, propagates timeline entries to every attendee/company page, extracts action items, creates bidirectional backlinks, then `gbrain sync`. This is where transcript value is actually realized — but it requires an agent harness (OpenClaw/Hermes/Claude Code), not just gbrain core. `POST /ingest` alone does **none** of this.

---

## Constraints

### Hard
- **Auth is mandatory**: OAuth bearer with `write` scope. No anonymous ingest. (Only `/webhooks/github` is anonymous, and it's HMAC-gated + sync-only.)
- **Content-type allowlist**: only the four text-shaped types. Transcripts/conversations must be sent as text/markdown/plain/html/json. Binary audio/video is rejected — the server must send **already-transcribed text**.
- **1 MB payload cap per request** (default). Long multi-hour transcripts can exceed this; either raise `GBRAIN_INGEST_MAX_BYTES` server-side or chunk per request (each chunk = its own page unless slugs are managed).
- **Server reachability**: `gbrain serve --http` defaults to bind `127.0.0.1` (v0.34.1+). To receive from an external sender, the operator must `--bind 0.0.0.0` (+ `--public-url`, + likely a tunnel/reverse proxy) and set `GBRAIN_HTTP_CORS_ORIGIN` / `GBRAIN_HTTP_TRUST_PROXY` appropriately.
- **`content_hash` must be valid SHA-256 hex** if you construct the event yourself — but for `POST /ingest` the *server* computes the hash from the raw body; the sender does **not** supply it. (The `IngestionEvent` schema with sender-supplied hash applies only to in-process/skillpack sources, not the HTTP route.)

### Soft
- **No enrichment at ingest** is a convention, not a bug: raw content lands under `inbox/` for later triage. If the user wants compiled analysis + entity propagation, that's Path B (agent-side), not a `/ingest` feature.
- **Slug discipline**: to avoid everything piling into `inbox/`, the sender should set `X-Gbrain-Slug` (e.g. `meetings/<date>-<topic>`, `sessions/<date>-<id>`).
- **Embed lag**: content isn't searchable until an embed pass runs; plan for autopilot or a cron `gbrain embed --stale`.
- One source-kind value (`webhook`) is hardcoded for `/ingest`; differentiate transcript vs AI-session via `X-Gbrain-Source-Id` and/or slug prefix.

### Unknowns (need external input) — see Open Questions

---

## Assumptions

| Assumption | Classification | Evidence |
|---|---|---|
| `POST /ingest` is GBrain's native, general-purpose webhook receiver for arbitrary content. | VERIFIED | `serve-http.ts:1777` route + `serve-http-ingest-webhook.test.ts` full spec. |
| It requires OAuth bearer with `write` scope; no anonymous access. | VERIFIED | `requireBearerAuth({ requiredScopes: ['write'] })` (`serve-http.ts:1780`); 401/403 tests. |
| Accepted content types are markdown/plain/html/json only; binary → 415. | VERIFIED | `INGEST_ALLOWED_CONTENT_TYPES` (`serve-http.ts:1765`) + 415 tests. |
| Default payload cap is 1 MB, tunable via `GBRAIN_INGEST_MAX_BYTES`. | VERIFIED | `serve-http.ts:1754-1760`. |
| Ingested content lands as a single brain page (under `inbox/` by default) with no transform/enrichment in v1. | VERIFIED | `ingest-capture.ts` — `importFromContent`, slug logic, header comments. |
| Sender does NOT supply `content_hash`/`IngestionEvent`; the route builds the event from raw body + headers. | VERIFIED | `serve-http.ts:1865-1886` constructs the event server-side. |
| Ingested pages aren't embedded inline; a separate embed pass is needed for search. | VERIFIED | `ingest-capture.ts:110-114` (`noEmbed` defaults true) + `live-sync.md`. |
| The richer meeting flow (compiled truth + entity propagation) is agent-side, not `/ingest`. | VERIFIED | `docs/guides/meeting-ingestion.md`, `skills/webhook-transforms/SKILL.md`. |
| `gbrain auth register-client … --scopes "read write"` mints client_credentials creds. | VERIFIED | `auth.ts:332-438` + E2E test `beforeAll`. |
| OAuth access tokens expire and must be re-minted; exact TTL is deployment-configured. | INFERRED | `tokenTtl` option + token sweep on startup; concrete value not read. |
| The target deployment will expose `serve --http` to the sending server (bind/tunnel done by operator). | UNKNOWN | No deployment topology found in repo for this project (DiDO). |
| Whether DiDO wants raw capture (Path A) or compiled/propagated ingestion (Path B). | UNKNOWN | Product decision; both are supported by different mechanisms. |

---

## Open Questions

1. **Architectural decision — Path A vs Path B (materially changes the build).**
   - **Path A — direct `POST /ingest`**: the new server formats each transcript/conversation as markdown and POSTs it. Simple, self-contained, no agent harness. Limitation: content lands raw under a slug; no diarization analysis, no per-attendee timeline propagation, no backlinks. Good enough if the goal is "everything is captured and searchable."
   - **Path B — agent-gateway ingestion**: the server (or source service) fires webhooks at an agent harness (OpenClaw/Hermes/Claude Code) that runs `meeting-ingestion`/`webhook-transforms` to produce compiled analysis + entity propagation. Realizes the full "brain" value the docs describe, but requires standing up/owning that agent layer — which is outside gbrain core and outside the "build a server that sends data" framing.
   → This is a good `/survey` candidate before planning.

2. **Deployment topology**: Where does `gbrain serve --http` run for DiDO (the 25-person Sierra team brain), and how will the sending server reach it (bind, public URL, tunnel, reverse proxy, CORS/trust-proxy env)? Multiplayer/team use may also raise auth-fanout questions (one OAuth client vs per-source clients).

3. **Payload sizing**: Will full transcripts exceed 1 MB? If so, decide between raising `GBRAIN_INGEST_MAX_BYTES` server-side vs chunking per request (and how to keep chunks on one page via slug).

4. **Searchability SLA**: Is there an embed pass (autopilot / cron `gbrain embed --stale`) in the target deployment, or does the server need to trigger/await embedding?

5. **Token lifecycle**: Confirm the configured OAuth token TTL and design refresh handling in the sending server.

---

## Recommended Next Steps

- **Resolve the architecture first** with `/survey` on Open Question #1 (Path A direct-`/ingest` vs Path B agent-gateway), since it determines the entire server design and whether an agent harness is in scope.
- Once Path is chosen, run **`/loop-plan`** with these inputs:
  - Target endpoint `POST /ingest` (Path A) — contract above is the integration spec.
  - Sender responsibilities: OAuth client_credentials token mgmt; markdown formatting (diarized for transcripts); per-record `X-Gbrain-Slug` (`meetings/…`, `sessions/…`); `X-Gbrain-Source-Id` to distinguish the two data types; payload chunking/limit handling; 202/4xx/5xx + idempotency handling; retry/backoff against the 100/10s rate limit.
  - Operator prerequisites: `gbrain serve --http --bind … --public-url …`, registered `write`-scope client, embed pass scheduled.
- If Path B is chosen, the plan shifts to the agent-harness layer and the `webhook-transforms`/`meeting-ingestion` skills — `POST /ingest` is then optional/secondary.
