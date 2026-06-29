# DiDO MVP Brief — reuse + design inventory (BLU-508..513, 519)

> Phase: Brief (research). One inventory for the whole authoring milestone.
> Grounded by reading gbrain source, not the plan. gbrain installed: 0.42.53.0.
> Authoring milestone: a schema pack (`dido-engagement`) + a skillpack (`dido-consulting`) + enrich/derivation conventions. NO edits to `gbrain/src`. Verification = gbrain validation gates.

## Run conventions (every stateful gbrain command)

- Prefix with `GBRAIN_HOME="$HOME/.gbrain-dido"` (isolated pglite validation brain; never the shared Supabase).
- `source ~/.zshrc` first in any non-interactive shell (PATH + `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`).
- `--help` is NOT a per-subcommand flag for `schema` verbs. `gbrain schema lint --help` is read as "lint the pack named --help" and errors. `gbrain skillpack <sub> --help` DOES work. To see schema verbs run bare `gbrain schema`.

## 1. Reuse inventory (search this first)

### 1a. Base schema pack — `gbrain/src/core/schema-pack/base/gbrain-base.yaml`

Top-level pack fields (copy this shape):
```yaml
api_version: gbrain-schema-pack-v1      # literal; required exactly
name: dido-engagement                    # /^[a-z0-9._-]+$/
version: 1.0.0                           # /^\d+\.\d+\.\d+$/ (3-part, NO 4th seg)
description: ...
gbrain_min_version: 0.42.0               # /^\d+\.\d+\.\d+(?:\.\d+)?$/ — 3 or 4 part. "0.42" FAILS
extends: gbrain-base                     # string | null (null = full override)
borrow_from: []
```
Manifest schema is `gbrain/src/core/schema-pack/manifest-v1.ts` (`SchemaPackManifestSchema`, `.strict()` — unknown keys reject).

Page type declaration (exact field names, `manifest-v1.ts:99-144`):
```yaml
page_types:
  - name: engagement
    primitive: entity        # closed enum: entity|media|temporal|annotation|concept (manifest-v1.ts:28). NO "expert" primitive
    path_prefixes: [engagements/]   # ARRAY; order = inferType priority, first match wins
    aliases: []              # query-closure expansion only; cap depth 4
    extractable: true        # boolean | ExtractableSpec struct; default false
    expert_routing: false    # boolean; default false; gates whoknows/find_experts candidacy
```

Link verb declaration (`LinkTypeSchema`, manifest-v1.ts:39-43). A verb has an OPTIONAL `inverse` string and an OPTIONAL `inference` block `{regex?, page_type?, target_type?}`. A verb with NO inference never auto-fires (valid but inert). Real base example:
```yaml
link_types:
  - name: attended
    inference: { page_type: meeting }     # type-bound auto-link
  - name: works_at
    inference: { regex: '\b(works? at|employed by|...)\b' }
  - name: related_to                        # no inference => declarative-only, must be written explicitly
```

`frontmatter_links` form (`FrontmatterLinkSchema`, manifest-v1.ts:146-150) — exactly three keys, NO direction/inverse field:
```yaml
frontmatter_links:
  - page_type: meeting        # the type of the page DECLARING the field
    fields: [attendees]       # array, min 1
    link_type: attended       # verb to materialize
```
Other top-level arrays a pack may carry: `takes_kinds`, `enrichable_types` (`{type, rubric?}`), `filing_rules` (`{kind, directory, examples}`), `phases` (validated against the closed CyclePhase union at load — see §3e), `calibration_domains`, `mapping_rules`. All optional.

### 1b. Authoring CLI surface (`gbrain schema`, real verbs)

- `gbrain schema validate <pack>` — shape check vs v1 schema.
- `gbrain schema lint <pack>` — file-plane rules by default; **`--with-db`** adds DB-plane rules (confirmed `src/commands/schema.ts:703` `args.includes('--with-db')`). Flag name VERIFIED.
- `gbrain schema use <pack>` — writes `~/.gbrain/config.json` schema_pack (destructive; needs GBRAIN_HOME).
- `gbrain schema sync` — DRY-RUN by default; **`--apply`** backfills `page.type` for rows matching pack prefixes. VERIFIED (bare `schema sync` printed `Mode: DRY-RUN`).
- `gbrain schema fork <src> <new>` / `init <name>` / `edit <name>` (prints on-disk path) — authoring verbs exist in 0.42.53 (not gated off). Plus granular `add-type --primitive <p> --prefix <dir/> [--extractable] [--expert]`, `add-link-type --inverse --page-type --target-type`, `set-extractable`, `set-expert-routing`, `review-orphans`, `graph`, `explain <type>`, `stats`.

### 1c. Skillpack reference — `gbrain/examples/skillpack-reference/`

Actual file layout (VERIFIED on disk):
```
skillpack.json            CHANGELOG.md   LICENSE   README   .gitignore
evals/reference-pack.judge.json
test/example.test.ts
e2e/example.e2e.test.ts
runbooks/bootstrap.md
skills/reference-pack/SKILL.md
skills/reference-pack/routing-eval.jsonl   # NOTE: routing-eval IS a literal .jsonl per skill
```
`skillpack.json` required fields (`manifest-v1.ts:119`): `api_version` (`gbrain-skillpack-v1`), `name` (`/^[a-z][a-z0-9-]{1,63}$/`), `version` (3 or 4-part semver, optional `-suffix`), `description`, `author`, `license` (SPDX), `homepage` (http(s) URL — REQUIRED and validated), `gbrain_min_version`, `skills` (non-empty array; each starts with `skills/`). Optional: `unit_tests`, `e2e_tests`, `llm_evals`, `routing_evals`, `runbooks.bootstrap`, `changelog`, `brain_resident`, `schema_pack`.

`SKILL.md` shape (gbrain's reference uses frontmatter `name / description / mutating / triggers[]`; gbrain's own bundled skills add `tools[] / writes_to[] / writes_pages`). Doctor's dim-2 requires only `name + description + triggers`. The plan's `## Contract` / `## Anti-Patterns` / `## Output Format` body headers are a convention, NOT doctor-enforced.

`gbrain skillpack doctor <pack-dir>` real flags: `[--quick|--full] [--fix] [--yes] [--json]`. `--quick` is the default structural sweep. **`--quick` VERIFIED.** What doctor actually checks (`src/core/skillpack/rubric.ts`, 10 binary dims):

CORE (all 5 must pass or tier=blocked):
1. `manifest_valid` — skillpack.json passes v1 validator
2. `skills_have_skill_md` — each skill dir has SKILL.md with frontmatter `name`, `description`, non-empty `triggers`
3. `routing_evals_present` — each skill has `routing-eval.jsonl` with **>= 5** lines (one JSON/line, `{intent, expected_skill}`)
4. `skills_have_unique_triggers` — no exact trigger phrase shared across skills (MECE, case-insensitive)
5. `changelog_present_and_current` — CHANGELOG has a `## [<version>]` entry matching manifest.version

BADGES (>=3 => community, all 5 => endorsed): 6 `unit_tests_present`, 7 `e2e_tests_present`, 8 `llm_eval_present` (a `*.judge.json` with **>=3** `cases`), 9 `bootstrap_runbook_present` (non-empty), 10 `license_present`. Dims 3,5,6,7,8,9,10 are `--fix` auto-scaffoldable; `--fix` needs `--yes` to write (no TTY confirm in this build).

### 1d. Existing skill idioms to match

- Repo `ingest-skills/*.skill` are ZIP archives (Claude/Anthropic skill bundles), not gbrain skill dirs — reference for capture, not for skillpack shape.
- `source-mock/` (Python, stdlib-only) is the filesystem ingest client for BLU-510: scans `sources/<source>/<YYYY-MM-DD>/<Title>.md`, POSTs to gbrain `POST /ingest`. Needs an OAuth client minted with `read write` scope (`gbrain auth register-client dido-ingest --grant-types client_credentials --scopes "read write"`).
- gbrain bundled skills to clone idioms from: `skills/schema-author/SKILL.md` (the schema verbs cheat-sheet), `skills/meeting-ingestion/SKILL.md` (frontmatter `triggers/tools/mutating/writes_to`, filing-rule preamble), `skills/enrich`, `skills/briefing`, `skills/query`, `skills/ask-user` (human-in-the-loop fallback for BLU-510), `skills/cron-scheduler` (BLU-509 scheduling). Read `skills/_brain-filing-rules.md` before any page-creating skill.

### 1e. Ingestion paths for BLU-510

- Type at write time: `parseMarkdown` does `coerceFrontmatterString(frontmatter.type) || inferTypeFromPack(filePath, activePack)` (`src/core/markdown.ts:135`). **Explicit `type:` frontmatter WINS over slug-prefix inference.** Prefix inference walks `page_types[].path_prefixes`, first match wins. VERIFIED.
- Provenance columns are first-class on `pages` (migrate.ts:3798-3801): `ingested_via TEXT`, `ingested_at TIMESTAMPTZ`, `source_uri TEXT`, `source_kind TEXT`. `put_page` accepts `source_kind / source_uri / ingested_via` but ONLY honors them when `ctx.remote === false` (trusted local caller); remote MCP/HTTP callers get server-stamped `mcp:put_page` (anti-spoof). So source-mock over HTTP `POST /ingest` gets server-stamped provenance; local `gbrain capture --file` / put can set it.
- `POST /ingest` (`src/commands/serve-http.ts:1778`): queues via a shared MinionQueue, stamps `source_id` from the OAuth client. Rate-limited, 1 MB default payload cap, rejects binary content. `gbrain serve --http [--port N]`.
- Sync: `gbrain sync [--repo <path>] [--source <id>] [--all] [--watch]` is git-to-brain incremental sync; `gbrain files sync <dir>` bulk-uploads a directory.
- Enrich / facts: `gbrain enrich` (src/commands/enrich.ts) is the LLM enrich step. Facts come from the `extract_facts` cycle phase / `gbrain extract` family (`extract.ts`, `extract-status.ts`). The enrich skill is the page-creating/filing path for BLU-510 (sets frontmatter so `frontmatter_links` materialize).

### 1f. Expertise + writes (BLU-513, 509/510/512)

- `gbrain whoknows <topic>` is a real CLI command (`src/cli.ts:1798` -> `src/commands/whoknows.ts`), backed by the read-scoped MCP op `find_experts`. It filters hybrid search to `expert_routing` page types via `SearchOpts.types`. Expertise Mapper just wraps it; the pack must set `expert_routing: true` on the routed types (MVP: `stakeholder` + `expertise`). Ranking = expertise x recency_decay x salience.
- `put_page` op (`src/core/operations.ts:724`): params `slug` (req), `content` (req, full markdown+frontmatter), optional provenance trio. CLI surface: `gbrain put <slug> [< file.md]` and `gbrain capture --file PATH --slug SLUG` (file-as-input, adds provenance). This is the write path for BLU-509/510/512.
- Backlinks read path: `gbrain backlinks <slug>` (incoming links), `gbrain graph <slug> [--depth N]`, `gbrain link <from> <to> [--link-type T]` for explicit edges (e.g. `similar_to`).

## 2. Data-layer / data-flow map

```
raw artifact (cowork/.. , fellow/..)
  -> source-mock POST /ingest  OR  gbrain sync/files sync       [provenance: source_kind/source_uri/ingested_via/ingested_at]
  -> enrich skill (LLM): creates/updates a TYPED page
        type set by slug prefix (engagements/, decisions/, ...) OR explicit `type:` frontmatter (frontmatter wins)
        + writes frontmatter fields (client:, engagement:, requested_by:, ...)
  -> on write/sync, FRONTMATTER_LINK_MAP materializes typed edges:
        edge points  fromSlug (the page declaring the field)  ->  targetSlug (referenced page)
        e.g. engagement page `client: clients/opa`  =>  engagement --client_of--> client
  -> reverse reads via backlinks: client's "owns/has engagements" view = `gbrain backlinks clients/opa`
  -> skills query: query / briefing / whoknows(find_experts over expert_routing types) / graph traversal
```
Net: pick the verb NAME to match the field that creates it and the direction the field points. The inverse view is a backlink query, never a declared inverse verb.

## 3. Headline facts (verbatim claim -> verdict)

1. **Status cannot be a pack-declared enum fact; it must be YAML frontmatter.** VERIFIED. The facts fence kind is a hardcoded enum `event|preference|commitment|belief|fact` (`src/core/facts-fence.ts:60`, re-declared from engine.ts, NOT pack-driven). The takes-table `kind` CHECK is `('fact','take','bet','hunch')` (migrate.ts:1196); a pack's `takes_kinds` widens THAT, not the facts kind. Typed-claim columns are numeric/text-scalar only: `claim_metric TEXT`, `claim_value DOUBLE PRECISION`, `claim_unit`, `claim_period` (migrate.ts:3315). No mechanism to add a `status` enum fact. So `engagement.status` {open,closed} and `opportunity.status` {open,won,lost} live in page frontmatter, enforced by skill/convention. (Minor citation correction: the relevant enum is FactKind in facts-fence.ts, not solely migrate.ts.)
2. **`frontmatter_links` has no inverse and no direction knob; name verbs after the field.** VERIFIED. `FrontmatterLinkSchema` is exactly `{page_type, fields[], link_type}` (manifest-v1.ts:146-150), `.strict()`. The engine's internal base `FRONTMATTER_LINK_MAP` carries a `direction` field (link-extraction.ts:749-767), but the PACK schema does not expose it, so a pack-declared frontmatter link can only materialize OUTGOING: `fromSlug` = the page declaring the field, `toSlug` = the referenced page (`extractFrontmatterLinks`, link-extraction.ts:1026-1090). A `LinkType` MAY carry an `inverse:` string for graph naming, but `frontmatter_links` itself cannot emit the reverse edge; reverse reads come from the source-scoped `get_backlinks` op / `gbrain backlinks`. So `owns` = the backlink view of `owned_by`.
3. **A verb with no inference rule never auto-fires.** VERIFIED. `inference` is optional on `LinkTypeSchema`; base ships inert verbs (`related_to`, `mentions`, `led_round` have no inference). Drive verbs from `frontmatter_links` (deterministic, zero-LLM); leave `similar_to` declarative-only (written via `gbrain link`).
4. **Skillpack doctor real requirements.** VERIFIED — see §1c. 5 core + 5 badges; community needs all core + >=3 badges. Routing-eval is a literal per-skill `routing-eval.jsonl` (>=5 lines), and the pack also ships `evals/*.judge.json` (>=3 cases) for the `llm_eval` badge. Both shapes coexist; the plan's "judge.json not routing-eval.jsonl" framing is half-right — the reference ships BOTH.
5. **BLU-509 derivation is a scheduled/on-demand skill, not a dream-cycle phase.** VERIFIED. `CyclePhase` is a closed hardcoded union (`src/core/cycle.ts:57-100`): lint, backlinks, sync, synthesize, extract, extract_facts, resolve_symbol_edges, patterns, recompute_emotional_weight, consolidate, propose_takes, grade_takes, calibration_profile, embed, orphans, purge, schema-suggest, extract_atoms, synthesize_concepts, conversation_facts_backfill, enrich_thin, skillopt. A pack's `phases:` can only OPT INTO existing phase names (validated against this union at load); it cannot add one. So `client-lifecycle-status` runs as a skill via `put_page`, on-demand now, scheduled once BLU-517 lands.

## 4. Early checkpoint flag (slice-first, before authoring skills)

Prove edge direction on the seed BEFORE writing skills. Sequence:
1. `gbrain schema validate dido-engagement` then `gbrain schema lint dido-engagement --with-db` (green).
2. `gbrain schema use dido-engagement`; `gbrain schema sync --apply` (backfill types).
3. File one enriched engagement page (e.g. `engagements/opa` with `client: clients/opa`) via enrich or `gbrain put`.
4. **Inspect direction:** `gbrain graph engagements/opa --depth 1` should show `engagement --client_of--> client`, and `gbrain backlinks clients/opa` should list the engagement. That backlink result IS the proof that the inverse (`owns`) reads correctly. If the verb fires the wrong way, rename the field/verb before authoring any skill that reads it.

(`GBRAIN_HOME="$HOME/.gbrain-dido"` on every step.)

## Open gaps

- Did not execute a live `schema use`/`sync --apply`/enrich round-trip on the seed (Brief is read-only); steps in §4 are the verification, run during BLU-508/510 execution. The exact `gbrain` list/filter command BLU-509 uses to enumerate clients by `status` frontmatter is unconfirmed (likely `gbrain query`/`search --types`); confirm at build. `gbrain enrich` internal contract (what it stamps automatically) read only at the command-name level.
