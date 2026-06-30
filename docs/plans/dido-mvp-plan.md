# Plan — dido-mvp (MVP, Store Intelligently)

Authoring milestone. Posture: authoring for every ticket. has-new-ui: false for every ticket. model: opus for every ticket. Verification is gbrain validation gates, not unit tests.

## Run conventions (every gate)

- 508-513 gates: prefix every gbrain command with `GBRAIN_HOME="$HOME/.gbrain-dido"` (isolated pglite validation brain). Assume `source ~/.zshrc` ran first (PATH + ANTHROPIC_API_KEY + OPENAI_API_KEY).
- 519 gates: target the DEFAULT shared brain. Do NOT set GBRAIN_HOME. Still assume `source ~/.zshrc` ran. Every command mutates shared state.
- Confirmed flags (from brief): `schema lint --with-db`, `schema sync --apply` (defaults to DRY-RUN, must pass --apply), `skillpack doctor --quick`. `--help` is not a per-subcommand flag for `schema` verbs.

## Slice-first directive

Prove the loop end-to-end before authoring breadth: 508 ontology -> 510 files ONE artifact -> 509 derives status -> ONE skill (Client Brief in 511) returns a grounded cited answer. Inside 508/510, run the edge-direction checkpoint before authoring any skill.

---

## BLU-508 — Author + activate `dido-engagement` schema pack (ontology)

- wave: 1 · depends-on: none
- complex?: no · posture: authoring · has-new-ui: false · model: opus
- acceptance (Done when):
  - `schema validate` + `lint --with-db` clean.
  - `schema use dido-engagement` is the active pack.
  - `sync --apply` backfills `pages.type` on existing pages.
  - New types + prefixes + verbs resolve. (Edge-direction proof deferred to 510's enriched page; `review-orphans` orphans expected until 510.)
- gates:
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema validate dido-engagement` -> exits 0, no errors.
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema lint dido-engagement --with-db` -> clean, no lint errors.
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema use dido-engagement` -> active pack = dido-engagement.
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema sync --apply` -> existing pages backfilled with `type`.
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema explain engagement` (and a spot of the 10 types) -> type + prefix + verbs resolve.

## BLU-510 — Capture, filing, and provenance (enrich)

- wave: 2 · depends-on: 508
- complex?: YES (inference-first enrich with human-in-loop fallback) · posture: authoring · has-new-ui: false · model: opus
- thin spec: Enrich skill is the automatic page-creating/filing path. Infer the client/engagement from artifact content and link it (create the engagement if absent); stamp `engagement:` frontmatter (including on `meeting` pages, so `context_for` materializes). Explicit `engagement:` hint used if present, never required. Low confidence -> ask via `ask-user` / open-questions list, never blocks filing (page always lands, only the uncertain link defers). Record a one-line rationale per inferred link. Stamp `status: open` on created engagements and opportunities (510 is 509's only input). On overlap with 512, enrich creates/updates; the skill annotates existing (dedupe by engagement + title/date).
- acceptance (Done when):
  - An ingested Cowork session + Fellow meeting (local seed) produce correctly-typed pages.
  - Auto-linked to engagement/client with owner + attendees; each inferred link carries a one-line rationale.
  - Created engagements carry `status: open`.
  - An unresolvable link surfaces as a human question, not a wrong guess or a dropped page.
- gates:
  - Run enrich over one curated client thread (e.g. Opa) -> the Cowork + Fellow artifacts become typed pages with `engagement:`/`client:` frontmatter + one-line rationale notes.
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain graph engagements/<slug> --depth 1` -> shows `engagement --client_of--> client` (edge direction proven).
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain backlinks clients/<slug>` -> lists the engagement (reverse/`owns` view reads correctly).
  - Inspect a created engagement page -> `status: open` present.
  - Force one unresolvable link -> surfaces as a queued human question; the page still lands.

## BLU-509 — Client lifecycle status (derived, with override)

- wave: 3 · depends-on: 508, 510
- complex?: no · posture: authoring · has-new-ui: false · model: opus
- acceptance (Done when):
  - A client page shows a derived `status` (or `status_override`) per the precedence rule (Active > Past > Prospect > Lost, first match wins).
  - Status transitions correctly as engagement/opportunity status changes; precedence applied (closed engagement + lost opportunity -> Past).
  - `status_override` skips derivation.
  - Clients are filterable by status.
- gates:
  - Run `client-lifecycle-status` skill over the seeded slice -> client `status` matches the rule.
  - Flip an engagement open->closed and re-run -> status transitions (Active -> Past).
  - Set `status_override` on a client and re-run -> override stands, derivation skipped.
  - Filter clients by `status` frontmatter (confirm exact `gbrain query`/`search --types` path at build) -> returns the expected set.

## BLU-511 — MVP skills: account + status (Client Brief, Weekly Account Health, Executive Summary)

- wave: 4 · depends-on: 508, 510 · (scaffolds the `dido-consulting` skillpack first)
- complex?: YES (first skill through doctor + pack scaffold rubric) · posture: authoring · has-new-ui: false · model: opus
- thin spec: `gbrain skillpack init dido-consulting`, clone `examples/skillpack-reference` layout (skillpack.json, CHANGELOG, LICENSE, test/, e2e/, runbooks/bootstrap.md, evals/<pack>.judge.json). Doctor needs BOTH per-skill `routing-eval.jsonl` (>=5 lines) AND `evals/*.judge.json` (>=3 cases), MECE-unique triggers across the pack, CHANGELOG `## [<version>]` matching manifest. All three skills read-only, cite source slugs, gap-flag missing data. Get one skill (Client Brief) green first, template the rest.
- acceptance (Done when):
  - `skillpack doctor --quick` green (5 core dims pass): routing-eval >=5 intents per skill, judge.json >=3 cases, MECE-unique triggers.
  - Client Brief returns a grounded, cited one-page brief against the seed; gap-flags missing data.
  - Weekly Account Health writes a cited report to `reports/weekly-account-health/<date>.md`.
  - Executive Summary returns a tight cited leadership brief.
- gates:
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain skillpack doctor dido-consulting --quick` -> green; routing-evals (>=5) + judge.json (>=3) present; triggers MECE-unique.
  - Invoke Client Brief against the seeded brain (e.g. the Opa thread) -> grounded cited answer, gap-flags missing data, does not invent.

## BLU-512 — MVP skills: meeting/risk/decision capture (Meeting Prep, Risk Review, Decision Log)

- wave: 4 · depends-on: 508, 510 · (run after 511 scaffolds the pack)
- complex?: no · posture: authoring · has-new-ui: false · model: opus
- acceptance (Done when):
  - `skillpack doctor --quick` stays green with these skills added (routing-evals >=5, judge.json >=3, MECE-unique triggers).
  - Each skill returns a grounded, cited answer against the seed; gap-flags missing data.
  - Decision Log capture writes a `decision` page with `requested_by:`/`approved_by:`/`engagement:` frontmatter; on overlap with enrich it updates the existing page (dedupe by engagement + title/date), no duplicate.
- gates:
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain skillpack doctor dido-consulting --quick` -> green with the new skills.
  - Invoke each skill against the seed -> grounded cited answer; Decision Log capture writes/updates one `decision` page, not a duplicate.

## BLU-513 — MVP skills: growth + reuse (Opportunity Finder, Proposal Writer, Deliverable Reuse, Expertise Mapper)

- wave: 4 · depends-on: 508, 510 · (run after 511 scaffolds the pack)
- complex?: no · posture: authoring · has-new-ui: false · model: opus
- acceptance (Done when):
  - `skillpack doctor --quick` stays green with these skills added (routing-evals >=5, judge.json >=3, MECE-unique triggers).
  - Each skill returns a grounded, cited answer against the seed; gap-flags missing data.
  - Expertise Mapper wraps `gbrain whoknows` over `expert_routing` types (stakeholder, expertise) and returns ranked people with why, cited.
- gates:
  - `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain skillpack doctor dido-consulting --quick` -> green with the new skills.
  - Invoke each skill against the seed -> grounded cited answer; `GBRAIN_HOME="$HOME/.gbrain-dido" gbrain whoknows <topic>` backs Expertise Mapper and returns ranked candidates.

## BLU-519 — Activate on the SHARED production brain

- wave: 5 · depends-on: 508, 509, 510, 511, 512, 513 (all green on the validation brain first)
- complex?: no · posture: authoring · has-new-ui: false · model: opus
- NOTE: gates run against the DEFAULT shared brain. Do NOT set GBRAIN_HOME. Still `source ~/.zshrc`. Every command mutates shared state.
- acceptance (Done when):
  - `dido-engagement` is the active pack on the shared brain; existing pages backfilled to real types.
  - `dido-consulting` skills answer grounded/cited against real accounts.
  - A tested rollback path is documented.
- gates (NO GBRAIN_HOME):
  - Back up first: `gbrain schema active` (record current pack) + `gbrain export` (or DB dump) captured.
  - `gbrain schema use dido-engagement` -> active.
  - `gbrain schema validate` -> exits 0; `gbrain schema lint --with-db` -> clean against real data.
  - `gbrain schema sync --apply` -> existing pages backfilled to real types.
  - `gbrain schema review-orphans` + spot `gbrain whoknows <topic>` / Client Brief queries on real accounts -> types/links resolve, nothing regressed.
  - `gbrain skillpack doctor dido-consulting` -> green on the shared brain.
  - Rollback documented + tested: `gbrain schema use <previous-pack>` + restore from snapshot.
