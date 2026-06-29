# DiDO MVP — Readiness & Execution Plan (BLU-508 … BLU-513)

> **Status:** draft for review
> **Date:** 2026-06-29
> **Purpose:** Determine whether BLU-508–513 are ready for an agent to execute, what to add to make them 100% ready, whether they fit one branch, and the best execution approach.
> **Grounding:** based on a code-level read of `gbrain/src/core/schema-pack/`, `src/core/skillpack/`, `src/core/cycle.ts`, `src/commands/serve-http.ts` (ingest), and the existing skills.

## Run conventions (read before any gbrain command)

Every executing agent must follow these. They are repeated in each MVP ticket so a fresh-context subagent can't miss them.

- **Point at the validation brain.** Prefix every gbrain command with `GBRAIN_HOME="$HOME/.gbrain-dido"`. Without it, gbrain falls back to `~/.gbrain` and the shared Supabase brain — destructive gates (`schema use`, `sync --apply`, backfills) would mutate shared state.
- **Load the shell first.** In any non-interactive tool shell, `source ~/.zshrc` before running gbrain. PATH and the API keys (`ANTHROPIC_API_KEY` for enrich/think, `OPENAI_API_KEY` for embeddings/retrieval) live there.
- **Phase 1 (Environment) is already done.** The isolated brain is stood up, seeded, and embedded (`docs/plans/dido-mvp-environment.md`). Do not redo it. Start at Phase 0 kickoff and skip straight to Brief/Plan/Execution.
- **Authoring posture.** Verification is gbrain validation gates (`schema validate`, `lint --with-db`, `skillpack doctor`, grounded answers against the seed), not unit tests.

## Operating principle: infer first, ask only when stuck

The brain should be as effortless to adopt as possible: drop data in, and it organizes itself. So the default posture for all linking and classification is **automatic AI inference, with no manual labeling required**. Explicit hints (e.g. an `engagement:` frontmatter field) are used *if present* but are never a precondition.

When the AI **can't confidently** resolve something — which engagement an artifact belongs to, who a person is — it does not guess and it does not silently drop the link. It **asks a human** through the existing human-in-the-loop path (gbrain's `ask-user` skill / the Slack loop from the hackathon brief) and folds the answer back in. This is a confidence-gated fallback, not a new subsystem.

Two things make aggressive auto-linking safe: a **confidence gate** (below a threshold, ask instead of link), and the fact that **every write is markdown-in-git** — a wrong inference shows up in a `git diff`, is auditable, and is trivially reversible. The failure mode of "infer by default" (confidently wrong links) is therefore visible and cheap to undo, not buried in a database.

## 1. Headline findings (these change the tickets)

Five facts from the codebase that an executing agent must be told, because it would otherwise get them wrong:

1. **A pack cannot declare a typed/enum fact.** `engagement.status` / `opportunity.status` / `client.status` **cannot** be a schema-enforced enum. The `## Facts` block is a structured table (`facts-fence.ts:16`: kind / confidence / claim_metric / claim_value / claim_unit / …), but the `kind` enum is hardcoded in the engine (`migrate.ts`) and the typed-claim columns are numeric-only, so a pack cannot add a `status` enum fact. Status must be a **YAML frontmatter field** on the page, with allowed values enforced by **skill/convention, not the engine**. *This rewrites the "extractable status fact" language in BLU-508/509.* (Earlier drafts said the facts fence is free-text prose; that was wrong. The conclusion stands for the reason above.)
2. **`primitive` and `path_prefixes` are required per page type and cannot be inferred.** `primitive` is one of exactly five (`entity | temporal | concept | annotation | media`) — there is no "expert" primitive. Each of our ten types needs an explicit primitive and directory prefix. These are decisions, not defaults.
3. **Link verbs only auto-create if you give them an inference rule.** A declared verb with no `regex` / `page_type` / `frontmatter_links` binding is valid but never fires — links must then be written explicitly. Drive almost every verb from **`frontmatter_links`** (deterministic, zero-LLM). One constraint: the pack `frontmatter_links` form is `{ page_type, fields, link_type }` (`manifest-v1.ts:146`) with **no direction/inverse field** — each edge materializes in the direction its frontmatter field points, and a pack cannot declare an inverse verb (engagement `owns` decision) from it. The reverse reading comes from backlink traversal, which gbrain supports; skills query the inverse direction via backlinks. So name each verb after the field that creates it. `similar_to` has no rule and stays declarative-only (the future pattern library writes it explicitly).
4. **Skills are pure markdown, but carry real packaging overhead.** A skill is a `SKILL.md` (frontmatter + body with `## Contract` / `## Anti-Patterns` / `## Output Format`). To pass `gbrain skillpack doctor`, each skill needs a routing-eval (≥5 intents) and MECE-unique triggers, and the pack needs `CHANGELOG`/`LICENSE`/tests/bootstrap. Match the real reference shape: `examples/skillpack-reference` ships `evals/<pack>.judge.json` (plus `LICENSE`, `CHANGELOG.md`, `skillpack.json`, `test/`, `e2e/`, `runbooks/bootstrap.md`), not a literal `routing-eval.jsonl` — author whatever `doctor` actually checks, confirmed by running it. `find_experts`/`whoknows` is a **built-in op, not a skill** — Expertise Mapper just wraps it (but needs `expert_routing` types in the pack).
5. **BLU-509's derivation runs as a scheduled skill, not a dream phase.** The dream-cycle phase list is a closed, hardcoded union — adding a real phase means forking `cycle.ts` + its tests. The clean, no-code path is a **scheduled agent/skill** that reads engagement/opportunity state and writes `client.status` back via `put_page`. It needs the always-on host (BLU-517) to be *scheduled*, but runs **on-demand today** with zero engine changes.

**Net:** nothing here requires forking `gbrain/src`. The entire MVP is **authoring** — a schema pack + a skillpack + enrich/filing conventions — committed as brain-resident artifacts. (One optional, non-blocking code gap exists: the ingest handler doesn't partition pages by `source_id`; irrelevant for our single shared open brain.)

## 2. One branch, separate commits? — Yes.

These six tickets are one cohesive unit (one ontology + one skillpack + the enrich/derivation glue) and should live on a **single feature branch** with a commit per ticket. Recommended sequence (each builds on the last):

| Commit | Ticket | Contents |
| --- | --- | --- |
| 1 | BLU-508 | `dido-engagement` schema pack: `dido-engagement.yaml` (page types, verbs, `frontmatter_links`, status conventions), `schema validate` + `lint --with-db` green, `sync --apply` backfill. |
| 2 | BLU-510 | Consulting enrich/filing skill + filing rules + provenance conventions (owner/attendees/source); seed-slice fixtures. |
| 3 | BLU-509 | `client-lifecycle-status` derivation skill (reads engagement/opportunity frontmatter → writes `client.status`), run on-demand. |
| 4 | BLU-511 | `dido-consulting` skillpack scaffold (`skillpack.json`, CHANGELOG, LICENSE, tests, bootstrap) + account/status skills. |
| 5 | BLU-512 | Meeting / risk / decision-capture skills. |
| 6 | BLU-513 | Growth / reuse skills. |

**Production rollout is a separate gated ticket (BLU-519).** The six commits above are proved on the isolated validation brain. Promoting the pack + skillpack onto the shared Supabase brain (real `schema use` / `sync --apply` over the team's pages, with backup + rollback) is BLU-519, blocked by 508–513. It does **not** set `GBRAIN_HOME` — it targets the default shared brain on purpose.

**Where the artifacts live:** commit the source pack + skillpack into the **DiDO repo** (brain-resident). Activation copies/writes to `~/.gbrain/` (`schema use` writes `~/.gbrain/config.json`; skillpack scaffolds into the workspace `skills/`), so include a short setup runbook. **Do not** edit `gbrain/src`. Dependency order inside the branch: 508 → (510, 509) → (511, 512, 513). The three skill commits are mutually parallel.

## 3. Per-ticket readiness

### BLU-508 — schema pack — **~80% ready**
Grounded and buildable (`schema fork gbrain-base dido-engagement` → edit `dido-engagement.yaml` → `validate`/`lint`/`use`/`sync --apply`). The pack file is `<pack-name>.yaml` (no `pack.yaml` convention), distributed as a `.gbrain-schema` tarball. `gbrain_min_version` must be three-part (`0.42.0`, not `0.42`); installed gbrain is 0.42.53.0. `fork`/`init`/`edit` are experimental verbs — if gated off, copy `gbrain-base.yaml` to `dido-engagement.yaml` and edit; confirm `--with-db`/`--apply` flag names via `--help`. **Add to the ticket:**
- The **per-type table** below (primitive + prefix + flags) — required, not inferable.
- **Status is frontmatter, not a fact** — drop the "extractable facts" wording; state `engagement.status` ∈ {open, closed} and `opportunity.status` ∈ {open, won, lost} live in page frontmatter, enforced by convention.
- The **verb-creation table** below (mostly `frontmatter_links`; `similar_to` declarative-only). Includes `context_for` (meeting → engagement) — without it meetings, the dominant artifact, have no typed link to their engagement.
- Note: `frontmatter_links` cannot express inverse verbs — each edge points the way its field points; query the reverse via backlinks (so `owns` is the backlink of `owned_by`).
- Note: declare every page type referenced by any verb to avoid `lint` errors; `extends: gbrain-base` (to reuse `meeting`/`person`); custom `extractable` types won't auto-extract via the put-page backstop pre-v0.43 — facts come from the explicit `extract-facts` / `extract_facts` cycle path.
- `expert_routing` is set on `stakeholder` + `expertise` only (MVP cut, narrower than the proposal); revisit if account-level `whoknows` routing is weak.
- Done-when nuance: `review-orphans` on the seed still shows raw notes as orphans until BLU-510's enrich files them — that routing is verified in BLU-510, not here.

Recommended ontology:

| Type | primitive | prefix | extractable | expert_routing |
| --- | --- | --- | --- | --- |
| client | entity | `clients/` | yes | no |
| engagement | entity | `engagements/` | yes | no |
| stakeholder | entity | `people/stakeholders/` | yes | **yes** |
| deliverable | annotation | `deliverables/` | yes | no |
| decision | temporal | `decisions/` | yes | no |
| risk | temporal | `risks/` | yes | no |
| opportunity | temporal | `opportunities/` | yes | no |
| expertise | concept | `expertise/` | no | **yes** |
| asset | concept | `assets/` | no | no |
| meeting | *(inherited from gbrain-base)* | `meetings/` | yes | no |

Recommended verb wiring:

| Verb | from → to | How it's created |
| --- | --- | --- |
| client_of | engagement → client | `frontmatter_links`: engagement `client:` |
| owned_by | deliverable/decision/risk → engagement | `frontmatter_links`: child `engagement:` (engagement-side `owns` is the backlink view) |
| context_for | meeting → engagement | `frontmatter_links`: meeting `engagement:` |
| requested_by | decision/deliverable → stakeholder | `frontmatter_links`: `requested_by:` |
| approved_by | decision → stakeholder | `frontmatter_links`: `approved_by:` |
| depends_on | deliverable/decision → deliverable/decision | `frontmatter_links`: `depends_on:` |
| blocked_by | engagement/deliverable/decision → risk | `frontmatter_links`: `blocked_by:` |
| expert_in | person → expertise | `frontmatter_links`: person `expert_in:` |
| renewal_for / expansion_for | opportunity → client | `frontmatter_links`: opportunity `renewal_for:` / `expansion_for:` |
| similar_to | engagement → engagement | declarative-only (future pattern library writes explicitly) |

### BLU-509 — client lifecycle status — **~75% ready**
The state model is decided (Prospect/Active/Past/Lost, derived, override, state-based). **Add:**
- **Representation:** client page frontmatter `status:` (derived) + `status_override:` (manual pin). Engagement/opportunity status are the frontmatter inputs from BLU-508.
- **Runtime:** a `client-lifecycle-status` **skill** run on-demand now (a Cowork/cron agent that queries engagement/opportunity pages per client and rewrites `client.status` via `put_page`, skipping when `status_override` is set). *Not* a dream phase (would require forking `cycle.ts`).
- **Derivation rule, explicit and ordered (first match wins):** (1) any engagement `status: open` → Active; (2) has engagement(s), all closed, none open → Past; (3) no engagement ever, an opportunity `status: open` → Prospect; (4) no engagement ever, opportunities all `status: lost` → Lost; else leave `status` unset. Precedence resolves overlap: a closed engagement + a separately-lost opportunity is **Past** (engagement history outranks opportunity-only states).
- **Inputs come from BLU-510:** the enrich step stamps `status: open` on engagements/opportunities it creates. This is a hard dependency (promoted to a `blocks` relation), not just `related`.
- **Filtering:** filter clients by reading the `status` frontmatter on `client` pages (same retrieval the account skills use); confirm the exact `gbrain` query/list path during build. No new index.
- Scheduling depends on BLU-517; on-demand works today.

### BLU-510 — capture / filing / provenance — **~70% ready**
Mechanism confirmed: type is set by **slug prefix or `type:` frontmatter** at write time; filing a raw `cowork/…` artifact into the ontology is an **LLM enrich step** that creates/updates the typed page and links it — not an automatic classifier. Provenance columns (`source_kind/source_uri/ingested_via/ingested_at`) are first-class; attendee `attended` links auto-materialize from body `[Name](people/slug)` references. Per the operating principle, this ticket is **infer-first with a human-in-the-loop fallback**. **Add:**
- **Inference is the primary path.** The enrich skill infers the client/engagement an artifact belongs to from its content and links it automatically (creating the engagement if absent). No manual labeling required.
- **Low confidence → ask (no formal threshold).** No numeric confidence gate — the enrich skill makes a qualitative judgment: link when confident, ask when not, via gbrain's `ask-user` skill / the Slack loop. Lives inside BLU-510 (no companion ticket). Two cheap guardrails: (a) low confidence **never blocks filing** — the artifact page is always created; only the uncertain *link* is deferred and queued as a question, so ingestion never stalls; (b) the skill records a **one-line rationale** for each inferred link on the page (timeline/provenance note) — near-zero cost, and it's what makes a wrong inference cheap to spot in a `git diff` and fix. The "ask" can start as a simple list of open questions in the run output and graduate to the Slack loop later, so it isn't blocked on Slack wiring.
- **Explicit hints are optional, not required.** An `engagement:` frontmatter field, if present, is used as a strong signal; its absence triggers inference, not a manual-labeling requirement.
- **Owner (resolved):** the ingest adapter (BLU-516) stamps frontmatter `owner: people/<slug>` — automatic provenance derived from the export, not user labeling.
- The filing target conventions (which raw prefix → which enriched type) and that the enrich skill sets frontmatter so `frontmatter_links` materialize the edges — including `engagement:` on `meeting` pages so `context_for` connects meetings to their engagement.
- **Status stamping (feeds BLU-509):** enrich stamps `status: open` on engagements and opportunities it creates. These are BLU-509's only inputs.
- **Page-creation ownership (vs BLU-512):** enrich is the automatic path for `decision`/`risk`/`deliverable` pages; the BLU-512 skills are the on-demand path. On overlap, enrich creates/updates and the skill updates the existing page (dedupe by engagement + title/date), never a duplicate.

### BLU-511 / 512 / 513 — the skills — **~60% ready**
Approach is sound (author as `dido-consulting` SKILL.md files). The blockers are **definitional, per skill**, plus a hard dependency: **every brain-reading skill needs the schema pack + a seeded brain to be demonstrably "done."** **Add per skill:**
- **Output format / template** (the consulting-specific shape — a product decision the code can't supply).
- **Trigger phrases** + the pack's routing-eval (≥5 intents), MECE-unique across the pack. Match the reference shape: `examples/skillpack-reference` ships `evals/<pack>.judge.json`, not a literal `routing-eval.jsonl` — author whatever `skillpack doctor` checks, confirmed by running it.
- **Interactive vs scheduled** (e.g. Weekly Account Health = scheduled; a scheduled custom handler is non-builtin and either needs host code via `worker.register` or routes through a generic `gbrain jobs submit` agent-turn — simplest is to run it as a Cowork scheduled task).
- **`writes_to:` + which page types/facts it reads** (pins the dependency on BLU-508/510).
- Expertise Mapper = thin wrapper over `gbrain whoknows`; needs `expert_routing` types (have them: stakeholder, expertise).

## 4. The cross-cutting prerequisite: a local validation brain seeded from real data

The skill tickets cannot be verified against an empty brain — they will return gap-flagged/empty answers. Two decisions resolve this without fabricating fixtures or touching the shared brain:

**Validation target — a local `pglite` brain, isolated from the shared Supabase.** Stand up a separate gbrain brain on the `pglite` engine under an isolated `GBRAIN_HOME`, so the destructive gates (`schema use`, `sync --apply`, backfills) never mutate the shared Supabase the team's MCP connectors point at. This is what every ticket's "Done when" runs against, and it lets us run and test fully independent of the shared host. `gbrain migrate --to pglite` confirms the engine is supported.

**Seed — a curated real slice, not fabricated fixtures.** `ryan-data` (`/Users/rr/dev/hackathon-dido/ryan-data`: ~324 Fellow meeting folders + 46 Cowork sessions, all markdown) is exactly the BLU-510 test bed. We do not invent a seed. Instead we pick one real client thread (e.g. Opa), ingest just those few artifacts via `source-mock`, and let BLU-510's enrich step file them into a typed `client` + `engagement` + `decision`/`risk` slice. That slice is the fixture BLU-509 and the skills (511–513) verify against, and it validates the ontology decisions against real data early. The full corpus can be ingested later; the curated thread is the minimum that makes the gates meaningful.

## 5. Best execution approach

1. **Slice first, not breadth first.** Build BLU-508, seed one real engagement, and prove the loop end-to-end — filing (510) → `frontmatter_links` materialize → status derivation (509) → a single skill (Client Brief) returns a grounded, cited answer. This de-risks every ontology decision before you write nine more skills.
2. **Stand up the skillpack scaffold once** (`gbrain skillpack init dido-consulting`, clone `examples/skillpack-reference` shape) and get one skill through `skillpack doctor` green, so the rubric overhead is paid once and templated.
3. **Fan out the remaining skills** (512/513) in parallel against the seeded brain.
4. **Run BLU-509 and any digests on-demand now;** wire them to a schedule only after the always-on host (BLU-517) lands.
5. **Encode the five headline facts into the tickets** before kicking off an agent — especially "status is frontmatter," "verbs via frontmatter_links," and "derivation is a scheduled skill." Without these an agent will try to declare enum facts and a custom dream phase and fail.
6. **Validation gates per commit:** `schema validate` + `schema lint --with-db` (508); a seeded round-trip showing links + derived status (509/510); `skillpack doctor --quick` green (511–513).

## 6. Decisions

**Resolved:**
- **Operating principle** — infer first, ask only when stuck; no manual labeling required (see principle section above).
- **Owner provenance** — the ingest adapter stamps frontmatter `owner: people/<slug>` (automatic, not labeling).
- **Engagement-linkage rule** — inference-first: the enrich skill infers the engagement from content and links automatically; explicit `engagement:` frontmatter is an optional hint; low confidence routes to the human-in-the-loop ask path.
- **BLU-509 run mode** — on-demand now (works today, zero new infrastructure); add a nightly schedule once the always-on host (BLU-517) lands.
- **Confidence handling** — no formal gate; qualitative low-confidence → ask, with a one-line rationale recorded per inferred link. Low confidence never blocks filing (page lands, only the link defers). Stays inside BLU-510.
- **Ontology + verb-wiring tables** (Section 3) — adopted and written into BLU-508/509/510.
- **Skill output formats + triggers** — drafted and written into BLU-511/512/513 (per-skill triggers, reads, output shape, interactive-vs-scheduled).
- **Validation target** — a local `pglite` brain under an isolated `GBRAIN_HOME`, kept separate from the shared Supabase so destructive gates don't touch shared state. Lets us run/test without the shared host (see §4).
- **Seed** — curated real slice from `ryan-data` (one client thread), filed via BLU-510's enrich step. No fabricated fixtures. Replaces the earlier "seed a thin real slice" framing (see §4).
- **Execution workflow** — run the set with the `lean-project` skill: one feature branch, one commit per ticket, an Environment phase that stands up the validation brain first, and authoring-posture verification (gbrain gates, not unit tests).

All decisions resolved; BLU-508–513 and BLU-516 hardened in Linear and ready for an agent.
