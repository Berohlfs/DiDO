# DiDO MVP — PR review

Branch: `ryan/dido-mvp` (base: `main`). One PR covering 7 tickets: BLU-508, 510, 509, 511, 512, 513, 519. All DONE.

The PR is not open yet. The next step is the reviewer's manual behavior and gate review, then the human opens the PR.

## 1. Overview

This branch lands Sierra's consulting brain on top of gbrain. It adds two authored artifacts and the conventions that connect them:

- `packs/dido-engagement` — a gbrain schema pack that makes the client engagement first-class (10 page types over 5 primitives, 11 link verbs), plus an enrich step (capture and filing with provenance) and a derived client-lifecycle skill.
- `packs/dido-consulting` — a publishable skillpack of 10 read and capture skills over that ontology (Client Brief, Weekly Account Health, Executive Summary, Meeting Prep, Risk Review, Decision Log, Opportunity Finder, Proposal Writer, Deliverable Reuse, Expertise Mapper).

The work was proven end-to-end on an isolated validation brain (`GBRAIN_HOME=$HOME/.gbrain-dido`, local pglite) then activated on the shared production brain (BLU-519). Posture is authoring: verification is the gbrain validation gates (validate, lint, doctor, sync, cited skill answers), not unit tests. No `gbrain/src` changes.

## 2. Artifact / net-new map (review focus)

One row per ticket. The net-new column is what a reviewer should scrutinize; reused rows follow known patterns and can be skimmed.

| Ticket | Files | Reused | Net-new (+ pattern + why existing didn't fit) — **scrutinize** |
|--------|-------|--------|----------------------------------------------------------------|
| BLU-508 | `packs/dido-engagement/dido-engagement.yaml`, `packs/dido-engagement/README.md`, ADR-001 | gbrain-base (`extends`); brief's confirmed manifest shape | **Hand-authored pack.yaml** (fork output had a wrong `extends:null` shape). **`meeting` redeclared locally** — lint validates `frontmatter_links.page_type` against the on-disk child manifest, not the extends-merged set, so `context_for` from `meeting` needs `meeting` declared locally. **`expert_in` originates on `stakeholder` not `person`** — `expert_routing` is scoped to stakeholder+expertise; an edge from inherited non-routed `person` would be inert in `whoknows`. |
| BLU-510 | `packs/dido-engagement/enrich/SKILL.md`, `enrich/filing-rules.md`, spec-510, ADR-002, `reports/enrich-open-questions.md` | dido-engagement pack (508); gbrain put/link/graph/backlinks; base `attended` auto-link; ask-user pattern; `_brain-filing-rules.md` | **Load-bearing finding: gbrain 0.42.53.0 does NOT auto-materialize custom-pack `frontmatter_links`.** `extractFrontmatterLinks` walks the hardcoded base `FRONTMATTER_LINK_MAP` (base verbs only); `frontmatterLinkTypeFromPack` is exported but never called. So all 10 dido verbs are created with explicit `gbrain link <from> <to> --link-type <verb>`. Frontmatter is still stamped as the declarative contract (509 input + forward-compat). `attended` is the exception (base verb, auto-links). **Infer-first + ask-when-stuck enrich**: no numeric confidence gate, never drops an artifact, defers the uncertain link only, one rationale note per inferred link for `git diff` auditability. |
| BLU-509 | `packs/dido-engagement/lifecycle-status/SKILL.md`, ADR-003 | enrich SKILL shape; backlinks traversal; ADR-001/002 findings | **Client lifecycle as a derived skill, not a fact or a dream phase.** gbrain can't carry status as a pack fact (facts kind is a closed enum, claim columns are numeric/text-scalar); `CyclePhase` is a closed 22-member union so a phase can't be added. Precedence ladder Active > Past > Prospect > Lost. **`status` (derived) vs `status_override` (human pin)** in separate fields so a re-run never clobbers an override. Filter path = enumerate `gbrain list --type client` then read `status:` (no frontmatter predicate exists). |
| BLU-511 | `packs/dido-consulting/**` (skillpack.json, LICENSE, CHANGELOG, README, runbooks/bootstrap, evals judge.json, test/e2e stubs, skills client-brief / weekly-account-health / executive-summary), spec-511, ADR-004 | skillpack-reference layout; backlinks/graph read-path; `status:` frontmatter | **Skillpack scaffold + doctor contract.** Doctor needs BOTH per-skill `routing-eval.jsonl` (≥5 intents) AND a pack `evals/*.judge.json` (≥3 cases) — they are separate dimensions, neither substitutes. **MECE trigger namespace reserved up front across 511/512/513** — doctor fails the whole pack on any exact-phrase collision. **Read-path traverses backlinks, not frontmatter_links** (same coupling as ADR-002: custom-pack edges are dormant, so the materialized backlink set is the only reliable enumeration). |
| BLU-512 | `packs/dido-consulting/skills/{meeting-prep,risk-review,decision-log}/**`, skillpack.json, CHANGELOG, judge.json, README (v0.1.0→0.2.0) | ADR-004 layout; ADR-002 dedupe + explicit-link-on-write | **First mutating skill (Decision Log).** Write path reproduces `auto_links=0` on `gbrain put`, then materializes the edge with explicit `gbrain link ... --link-type approved_by`. **Enrich vs 512 dedupe boundary** keyed on `engagement + title/date` — updated existing `decisions/2025-07-14-default-ai-model` instead of creating a duplicate. No new ADR (covered by ADR-002). |
| BLU-513 | `packs/dido-consulting/skills/{opportunity-finder,proposal-writer,deliverable-reuse,expertise-mapper}/**`, skillpack.json, CHANGELOG, judge.json (v0.2.0→0.3.0) | ADR-001 expert_routing scope; ADR-004 read-path | **Expertise Mapper wraps real `gbrain whoknows`** (Scott Wayman 0.306, Andrew Willett 0.287), shaped with WHY + gap-flags thin coverage. Opportunity Finder, Proposal Writer (DRAFT, grounded in decisions), Deliverable Reuse (gap-flags rather than surfacing a note as a deliverable). All read-only, wrote nothing. No new ADR. |
| BLU-519 | `packs/` source (no `gbrain/src`); `docs/plans/dido-mvp-blu519-rollout-runbook.md` | the full pack + skillpack; gbrain schema/skillpack CLI | **Shared-brain activation** (targets shared brain on purpose, no `GBRAIN_HOME`). Backup → validate → lint `--with-db` → `schema use` → sync dry-run → `sync --apply` (applied=0) → doctor. **Follow-up surfaced:** pack `extends gbrain-base` while the shared brain runs `gbrain-base-v2` — lint clean today, re-base before team reliance. |

Net-new inventory in one place (cross-check nothing is missed): hand-authored `dido-engagement.yaml`; local `meeting` redeclaration; `expert_in` on stakeholder; the no-auto-materialize finding + explicit-`gbrain link` edge convention; infer-first enrich with rationale-note auditability; derived lifecycle skill with `status`/`status_override` split; skillpack dual-eval contract; MECE trigger namespace; backlinks read-path; Decision Log mutating write path; Expertise Mapper over real `whoknows`; shared-brain flip + rollback runbook.

## 3. Gate results

All gates ran on the isolated validation brain except BLU-519 (shared brain on purpose). All green.

| Ticket | Gate | Result | Note |
|--------|------|:------:|------|
| BLU-508 | `schema validate` | green | exit 0 |
| BLU-508 | `schema lint --with-db` | green | clean |
| BLU-508 | `schema use` | green | pack active |
| BLU-508 | `schema sync --apply` | green | would_apply=0 (no typed pages until 510 — expected) |
| BLU-508 | `schema explain` | green | — |
| BLU-510 | enrich run → typed pages | green | client 1, engagement 1, meeting 5, decision 2, risk 1, opportunity 1, stakeholder 2, person 2, note +2 |
| BLU-510 | `graph engagements/abstudios-sierra --depth 1` | green | edge direction proven: engagement `--client_of-->` clients/abstudios (+ `--blocked_by-->` risk) |
| BLU-510 | `backlinks clients/abstudios` | green | reverse reading: engagement (client_of) + opportunity (expansion_for) |
| BLU-510 | frontmatter contract | green | engagement + opportunity stamped `status: open`; cowork note → `note`, link deferred + queued |
| BLU-509 | derive lifecycle | green | clients/abstudios → `status: Active` (engagement open) |
| BLU-509 | transition | green | engagement open→closed → Past; restored → Active |
| BLU-509 | override | green | `status_override: Past` skips derivation; removed → re-derives Active |
| BLU-511 | `skillpack doctor --quick` | green | ★ 10/10 [endorsed], 5 core + 5 badges |
| BLU-511 | Client Brief cited answer | green | cited one-pager on ABStudios, gap-flags severity/touchpoints, invents nothing (slice proven 508→510→509→511) |
| BLU-512 | `skillpack doctor --quick` | green | ★ 10/10, 6 skills, MECE confirmed |
| BLU-512 | capture skills cited + dedupe | green | Decision Log updated existing page (no duplicate), `auto_links=0`, explicit link → `--approved_by-->` people/ryan-ramirez |
| BLU-513 | `skillpack doctor --quick` | green | ★ 10/10, 10 skills, MECE confirmed |
| BLU-513 | growth/reuse skills cited | green | Opportunity Finder, Expertise Mapper over real `whoknows`, Deliverable Reuse + Proposal Writer gap-flag honestly |
| BLU-519 | shared-brain flip | green | 822-page backup → validate (exit 0) → lint `--with-db` (warnings only) → `sync --apply` applied=0 → review-orphans 0 → doctor 10/10 → stats 822/14684 unchanged (zero data loss) |

## 4. Architecture & decisions

- [ADR-001 — dido-engagement ontology](../adr/ADR-001-dido-engagement-ontology.md): 10 page types over 5 primitives, 11 verbs from `frontmatter_links` with no inverse (reverse via backlinks); `expert_in` on stakeholder; status in frontmatter, not a pack fact.
- [ADR-002 — enrich filing by inference](../adr/ADR-002-enrich-filing-inference.md): infer-first + ask-when-stuck, no numeric gate, never drop an artifact, rationale-note auditability. Records the load-bearing finding that custom-pack `frontmatter_links` do not auto-materialize in 0.42.53.0, so edges are created with explicit `gbrain link`.
- [ADR-003 — client lifecycle derivation](../adr/ADR-003-client-lifecycle-derivation.md): derived label via a skill (not a fact, not a dream phase); precedence Active > Past > Prospect > Lost; `status` vs `status_override`.
- [ADR-004 — dido-consulting skillpack](../adr/ADR-004-dido-consulting-skillpack.md): layout cloned from the reference; doctor needs routing-eval AND judge.json; MECE trigger namespace across 511/512/513; read-path traverses backlinks, not frontmatter_links.

## 5. Work summary (lines added, by area)

From `git diff main...ryan/dido-mvp --numstat`. Insertions only (the branch is all additions). 47 files, 2899 lines.

| Area | Files | Lines | % |
|------|------:|------:|--:|
| Schema / pack config (`*.yaml`, skillpack.json, judge.json, LICENSE, CHANGELOG, README, runbooks) | 8 | 389 | 13% |
| Skills (`SKILL.md`, `routing-eval.jsonl`, enrich/lifecycle/filing-rules) | 24 | 1301 | 45% |
| Tests (presence stubs) | 2 | 19 | 1% |
| Documentation (`docs/**`: ADRs, plans, specs, brief) | 11 | 1152 | 40% |
| Reports / curated data (`reports/**`) | 2 | 38 | 1% |
| **TOTAL** | **47** | **2899** | **100%** |

Skills and documentation are the bulk, as expected for an authoring milestone. The only `.ts` files are the two empty presence stubs doctor requires; there is no executable prod code.

## 6. Follow-ups / risks

- **Base mismatch (gbrain-base vs gbrain-base-v2).** The pack `extends gbrain-base`; the shared brain runs `gbrain-base-v2`. Lint `--with-db` is clean today and the flip retyped 0 pages, but consider re-basing the pack on `gbrain-base-v2` before the team relies on it, so shared types (person, company, meeting, concept) resolve identically. Capture as a follow-up ticket.
- **Deferred enrich open questions.** `reports/enrich-open-questions.md` holds the links enrich could not infer with confidence (e.g. the cowork note's engagement). These need a human pass.
- **`whoknows` returns `[]` on the demo corpus.** The shared brain holds Acme/Snackably demo data with no stakeholder/expertise pages, so Expertise Mapper gap-flags until real stakeholder and expertise pages are filed under the dido prefixes. The read skills light up as that data lands.
- **Edge freshness coupling.** Because dido edges are created with explicit `gbrain link`, any relation whose edge was never materialized is invisible to the read-path. If a future gbrain wires the pack resolver, the explicit calls become redundant rather than wrong.
