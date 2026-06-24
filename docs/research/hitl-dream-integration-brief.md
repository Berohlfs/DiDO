# Research Brief: Human-in-the-Loop Integration with the gbrain Dream Architecture

**Date**: 2026-06-24
**Requirement**: Add a human-in-the-loop (HITL) layer that flags contradictory / review-needed / context-missing documents and document interactions, routes them to the relevant user(s), creates review "tickets", and feeds the human's resolution back into the dream cycle.
**Verdict**: **Ready for Planning** — with one material design decision (user-routing substrate) that should go through `/survey` before `/loop-plan`.

---

## Scope

**In scope (questions answered):**
1. How the "dream" architecture works — what it is, what runs it, its phases, coordination.
2. Where the dream cycle already detects contradictions / things-needing-review.
3. What "ticket"/queue-like primitives already exist to hold flagged items.
4. How multiplayer/users are modeled — can the system identify "the relevant user" to ask?
5. How a resolution gets fed back into the dream queue / brain.

**Out of scope (deferred to planning/later):**
- UI/UX for the ticket surface (web admin, Slack, Linear, email).
- The LLM prompts/judging quality for *deciding* what needs review (the probe already exists; tuning it is separate).
- Auth/OAuth client provisioning flows (assumed already configured per the multiplayer tutorial).
- Cost/eval methodology for any new LLM calls.

**Depth budget used:** 6 files read + 2 parallel Explore agents (multiplayer/identity; queue/ticket primitives). Within bounds.

---

## Landscape

**Tech stack:** TypeScript on Bun. CLI (`src/cli.ts`) + MCP server (`src/mcp/server.ts`) are both generated from a single contract (`src/core/operations.ts`, ~90 ops). Pluggable storage engine: PGLite (embedded Postgres/WASM, default) or Postgres + pgvector (Supabase). Schema DDL lives in the `MIGRATIONS` array in `src/core/migrate.ts` (+ `src/schema.sql`).

**Two orthogonal organizing axes (load-bearing for this work):**
- **Brain** = which database. **Source** = which repo inside the database (`source_id` TEXT). Multi-tenancy in the "company brain" is achieved by **source isolation**, not by per-person ownership.

**The dream cycle (`gbrain dream` → `src/core/cycle.ts:runCycle`):**
- `gbrain dream` (`src/commands/dream.ts`) is a thin alias over `runCycle`. Three entry points converge on `runCycle`: the `dream` CLI (one-shot/cron), `gbrain autopilot` (daemon, `src/commands/autopilot.ts` + `autopilot-fanout.ts`), and the durable `autopilot-cycle` minion-job handler (`src/commands/jobs.ts:~1622`).
- `runCycle` executes an ordered list of **phases** (`ALL_PHASES`, `src/core/cycle.ts:101`). Each phase is tagged per-source or global (`PHASE_SCOPE`, `cycle.ts:210`). Coordination is a DB lock row `gbrain_cycle_locks` (30-min TTL, refreshed between phases) on Postgres, or a `~/.gbrain/cycle.lock` file on PGLite.
- Phases relevant to HITL (in order): `synthesize` (transcripts→pages), `extract` / `extract_facts` / `extract_atoms` (knowledge units), **`propose_takes`** (LLM proposes gradeable claims to a review queue), **`grade_takes`** (judges proposals; auto-resolve OFF by default), `consolidate` (writes temporal `valid_until`), and the global contradiction probe phase (`nightly_probe` / `eval_contradictions`).

**The contradiction detector already exists** (`docs/contradictions.md`, `src/core/eval-contradictions/`): `gbrain eval suspected-contradictions` samples retrieval, runs an LLM judge over candidate pairs, and emits findings with a 6-member verdict enum (`no_contradiction | contradiction | temporal_supersession | temporal_regression | temporal_evolution | negation_artifact`), a severity (`low|medium|high`), and a paste-ready `resolution_command`. **Hard invariant: the probe NEVER mutates the brain** (`auto-supersession.ts` — "NEVER auto-applies"); it only writes to `eval_contradictions_runs` + `eval_contradictions_cache`. The operator decides.

---

## Patterns & Conventions

**Existing "ticket"/queue primitives (the HITL system should reuse these, not invent):**

| Primitive | Storage | Shape / status model | Already HITL? |
|---|---|---|---|
| **Take proposals** (`propose_takes` phase) | `take_proposals` table (`migrate.ts:~3408`) | `status` ∈ `pending\|accepted\|rejected\|superseded`; `claim_text, kind, holder, weight, domain, model_id, proposed_at, acted_at, acted_by, promoted_row_num`; idempotency key `(source_id, page_slug, content_hash, prompt_version)` | **Yes** — closest existing analog to a "review ticket"; accept/reject via `gbrain takes propose --accept/--reject N` |
| **Contradiction findings** | `eval_contradictions_runs` + `_cache` only | finding = `{verdict, severity, resolution_kind, resolution_command, confidence}`; NOT persisted as an actionable queue | Partial — emits paste-ready commands, but no ticket lifecycle |
| **Anomalies** (`find_anomalies`, v0.29) | computed on-demand, **not persisted** | statistical cohort spikes `{cohort_kind, cohort_value, count, baseline_mean, sigma_observed, page_slugs[]}` | No — signal, not a queue |
| **Minion jobs** | `minion_jobs` table (`migrate.ts:178`) | durable queue: `name, queue, status(waiting/active/...), data(JSONB), priority, delay_until, idempotency_key, parent_job_id, result`; submit via `gbrain jobs submit <name> --params JSON` | This is the **enqueue/worker substrate** for feeding work into a cycle |

**Resolution kinds the probe already classifies** (`auto-supersession.ts`): `takes_supersede`, `takes_mark_debate`, `dream_synthesize`, `temporal_supersede`, `log_timeline_change`, `flag_for_review`, `manual_review` — each maps to a concrete CLI command.

**Feeding a resolution back into the brain/dream (existing write paths):**
- `gbrain takes supersede/mark-debate/resolve <slug> --row N` → mutates canonical `takes` (markdown fence + DB row; `superseded_by`, `active`, `resolved_*` columns on the `takes` table, `migrate.ts:1191`).
- `gbrain dream --phase synthesize --slug <slug>` or `--input <file>` → re-runs synthesis scoped to one entity/file.
- Accepting a take proposal writes the claim into the canonical `takes` fence (DB + markdown), which subsequent extract/embed phases pick up.
- `minion_jobs` submit `autopilot-cycle` with a `phases` subset + `source_id` → re-triggers a scoped cycle run.
- `volunteer_context` / push-context (`src/core/context/volunteer.ts`, `docs/guides/push-context.md`) is **read-side** (brain volunteers pages into a prompt) — NOT a write-back path; logs to `context_volunteer_events`.

**Trust boundary convention:** every op carries `scope: read|write|admin`; `OperationContext.remote` is fail-closed (anything not strictly `false` is untrusted). The contradiction `find_contradictions` MCP op is read-scope and deliberately NOT in the subagent allowlist (user-initiated only). Any new HITL write op must respect this.

**Reusable utilities to build on:** `runCycle` phase model + `PHASE_SCOPE` (add a phase the canonical way), `take_proposals` lifecycle (template for a ticket table), `minion_jobs` queue (`queue.add`), `AuthInfo`/`sourceScopeOpts(ctx)` for source-scoped access, the `MIGRATIONS` array for any new table.

---

## Constraints

### Hard
- **Engine parity:** any new table/SQL shape must land in BOTH `postgres-engine.ts` and `pglite-engine.ts`, pinned by `test/e2e/engine-parity.test.ts`. New columns/indexes referenced early go in the bootstrap probe set.
- **Contract-first:** new operations must be added to `src/core/operations.ts` (CLI + MCP generated from it), each with `scope` + optional `localOnly`.
- **Migrations discipline:** schema DDL only in the `MIGRATIONS` array in `migrate.ts`; `CREATE INDEX CONCURRENTLY` needs `transaction: false`.
- **JSONB rule:** never `JSON.stringify` into a `::jsonb` cast (postgres.js double-encodes; PGLite hides it). Use raw objects / `executeRawJsonb` / `$N::text::jsonb`.
- **Source isolation:** every read-side op routes through `sourceScopeOpts(ctx)`; never hand-roll `source_id` filtering (cross-source leak risk).
- **"Probe never mutates the brain" invariant:** auto-supersession NEVER auto-applies. A HITL system that auto-writes resolutions would violate the spirit of this unless gated behind explicit human action.
- **Trust fail-closed:** `OperationContext.remote` required; remote/agent callers untrusted by default.

### Soft
- Add new background work the canonical way: a `runCycle` phase (pack-gated via the active pack's `phases:` declaration) and/or a `minion_jobs` handler — all three cycle entry points must stay convergent on `runCycle`.
- Bulk/long operations stream progress to **stderr** via `src/core/progress.ts` (stdout stays clean for `--json`).
- Privacy: public artifacts must scrub real names; the contradiction/redaction gates already model the expected caution around private fence data.
- Auto-resolve defaults OFF (`grade_takes` precedent) — HITL should preserve human-gated application.

### Unknowns (need external input)
- **Who is "the relevant user"?** (see Open Questions — this is the one material gap).
- Where tickets should surface (admin UI vs MCP op vs external system like the connected Linear workspace) — product decision, not a code fact.

---

## Assumptions

| Assumption | Classification | Evidence |
|---|---|---|
| "Dream" = the brain-maintenance cycle (`runCycle`), run by `dream`/`autopilot`/`autopilot-cycle` job | **VERIFIED** | `src/commands/dream.ts:1-32`, `src/core/cycle.ts:1-46` |
| The cycle is a fixed ordered phase pipeline; new background work is added as a phase | **VERIFIED** | `ALL_PHASES` + `PHASE_SCOPE` `cycle.ts:101,210`; pack-gated phases (`extract_atoms`) |
| Contradiction detection already exists and is non-mutating (emits paste-ready commands only) | **VERIFIED** | `docs/contradictions.md:136-143`, `eval-contradictions/auto-supersession.ts` "NEVER auto-applies" |
| `take_proposals` is the existing review-queue/ticket analog with pending/accepted/rejected lifecycle | **VERIFIED** | `migrate.ts:~3408`, `cycle/propose-takes.ts`, `commands/takes.ts` accept/reject |
| `minion_jobs` is the durable enqueue substrate to feed work into a cycle/worker | **VERIFIED** | `migrate.ts:178`, `core/minions/queue.ts`, `commands/jobs.ts` handlers incl. `autopilot-cycle` |
| Multiplayer = **source isolation**, enforced at SQL via `source_id` + OAuth client scopes; no `users` table | **VERIFIED** | `docs/tutorials/company-brain.md`, `oauth_clients`/`access_tokens` in `schema.sql`, `sourceScopeOpts` `operations.ts:417` |
| There is **no page-level provenance** (`created_by`/`captured_by`); only `takes.holder` + `takes.resolved_by` carry a per-claim "who" | **VERIFIED** | `pages` schema (`schema.sql:87`) has no creator col; `takes.holder/resolved_by` `migrate.ts:1191` |
| `mcp_request_log` records token_name+operation but does NOT back-link to the modified page | **VERIFIED** | `schema.sql:616-626` |
| A resolution can be fed back via `takes supersede/resolve`, `dream --phase synthesize --slug/--input`, accepting a proposal, or a scoped `autopilot-cycle` job | **VERIFIED** | `commands/takes.ts`, `commands/dream.ts:120-156`, `take_proposals` promote path, `jobs.ts` handler |
| OAuth `client_name` (e.g. "alice-example") is the available human-routing handle today | **INFERRED** | `oauth_clients.client_name` + `AuthInfo.clientName`; no evidence it maps to a real contactable identity (email/Slack) |
| The connected Linear MCP workspace could host the external "ticket" surface | **INFERRED** | Linear MCP tools are connected in this session; no in-repo integration exists |

---

## Open Questions

**The one material decision (blocks a clean architecture, not the investigation):**

> **How does the HITL system map a flagged item → "the relevant user(s)" to ask?**
> The brain has **no per-document provenance** and **no users table**. The only "who" signals that exist are: (a) the **source** a page belongs to → the OAuth client(s) scoped to write that source (`oauth_clients.client_name` / `federated_read`); (b) per-claim **`takes.holder`** / `takes.resolved_by` (opt-in, takes-only); (c) `mcp_request_log.token_name` (operation log, not page-linked). None of these is guaranteed to be a *contactable human identity* (email/Slack handle).

Candidate resolutions to weigh in `/survey` (do not pick here):
- Route by **source ownership** (page.source_id → owning OAuth client/team).
- Add a **page-level provenance column** (`created_by`/`captured_by`) captured from `AuthInfo` at write time (mirrors the `takes.holder` pattern).
- Route by **`takes.holder`** for take/claim contradictions specifically.
- **Manual assignment** (ticket created unassigned; a human triages) — lowest substrate requirement.

Secondary (product, not blocking): **where do tickets live?** New `review_tickets` table + admin UI/MCP op, vs. push to the connected **Linear** workspace, vs. reuse/extend `take_proposals`.

These are *design decisions*, not missing facts — the scope, primitives, and constraints are all verified — so the brief is Ready for Planning, with the routing decision flagged for a focused survey.

---

## Recommended Next Steps

1. **`/survey`** the one material decision first: *"How should the HITL system map a flagged document/interaction to the relevant user(s) to ask, given gbrain has source isolation + OAuth client scopes but no page provenance and no users table?"* — survey the 4 candidate routing approaches above against the engine-parity / source-isolation / fail-closed constraints.
2. **`/loop-plan`** once routing is chosen, with these verified inputs:
   - Flagging engine: reuse the existing **contradiction probe** (`eval-contradictions`) + the `propose_takes`/anomalies signals; add a "needs-context" detector if required.
   - Ticket store: model on **`take_proposals`** lifecycle (or a new `review_tickets` table via the `MIGRATIONS` array), engine-parity from day one.
   - Surface: new contract-first op in `operations.ts` (read to list, write/admin to resolve) and/or the **Linear** MCP integration.
   - Feedback path: human resolution → existing write paths (`takes supersede/resolve`, accept-proposal, `dream --phase synthesize --slug`) → re-enqueue a scoped **`autopilot-cycle`** minion job so the dream cycle re-incorporates the input.
   - New background detection should be added as a canonical **`runCycle` phase** (pack-gated) so `dream`/`autopilot`/the job handler all converge.
