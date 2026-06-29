# Baton — dido-mvp

- milestone: MVP — Store Intelligently (Linear milestone `df3ce41c`, project DiDO)
- branch: ryan/dido-mvp
- namespace: dido-mvp
- posture: authoring  # gbrain validation gates are the verification, not unit tests
- validation target: docs/plans/dido-mvp-environment.md — isolated from shared/prod? **yes** (`GBRAIN_HOME="$HOME/.gbrain-dido"`, local pglite, NOT the shared Supabase)

## Run conventions (every gbrain command for 508–513)
- Prefix with `GBRAIN_HOME="$HOME/.gbrain-dido"` (else hits shared Supabase brain).
- `source ~/.zshrc` first in any non-interactive shell (PATH + ANTHROPIC_API_KEY + OPENAI_API_KEY).
- BLU-519 is the EXCEPTION: it targets the shared brain on purpose — do NOT set GBRAIN_HOME; still `source ~/.zshrc`.
- Verified at kickoff: gbrain 0.42.53.0; validation brain = 7 pages / 218 chunks / 218 embedded; both keys set.

## Tickets (the DAG / wave order)
- wave 1: BLU-508 — Author + activate `dido-engagement` schema pack (ontology)
- wave 2: BLU-510 — Capture, filing, and provenance (enrich step)
- wave 3: BLU-509 — Client lifecycle status (derived, with override)
- wave 4: BLU-511, BLU-512, BLU-513 — `dido-consulting` skillpack (logically parallel; run sequentially for clean per-ticket commits — 511 scaffolds the pack first)
- wave 5: BLU-519 — Promote pack + skillpack to the SHARED production brain (gated on 508–513 green)
- depends-on edges: 510→508; 509→{508,510}; 511→{508,510}; 512→{508,510}; 513→{508,510}; 519→{508,509,510,511,512,513}

## Slice-first directive (from execution plan §5 + user)
Prove the loop end-to-end before authoring breadth: 508 (ontology) → 510 files ONE artifact → 509 derives status → ONE skill (Client Brief, in 511) returns a grounded cited answer. Early checkpoint inside 508/510: confirm `frontmatter_links` edges materialize in the direction skills expect (each edge points the way its field points; reverse via backlinks) BEFORE authoring skills.

## Pointers
- execution plan: docs/mvp-execution-plan.md  (Run conventions block + §3 tables + §5)
- headline facts: docs/mvp-execution-plan.md §1 (5 facts) — carried into the brief
- proposal (templates): docs/consulting-brain-proposal.md (§7 ontology, §8 lifecycle, §10 decision template)
- environment runbook: docs/plans/dido-mvp-environment.md
- brief: docs/research/dido-mvp-brief.md  (DONE — reuse shapes + 5 verified facts + confirmed CLI flags)
- plan: docs/plans/dido-mvp-plan.md  (DONE — per-ticket gates + acceptance; 510 & 511 marked complex → thin spec)
- tracker: docs/plans/dido-mvp-tracker.md  (DONE)

## Decisions
- (none yet — ADRs accrue during execution)

## Phase log
- P0 Kickoff: done → this baton; branch ryan/dido-mvp cut; 7 tickets imported from Linear
- P1 Environment: done (pre-provisioned) → docs/plans/dido-mvp-environment.md (validation brain reachable + embedded, verified at kickoff)
- P3 Plan: done → docs/plans/dido-mvp-plan.md + tracker. Complex (thin spec): BLU-510, BLU-511. 509 build-time TODO: confirm exact filter-by-frontmatter path (`gbrain query` vs `search --types`).
- P2 Brief: done → docs/research/dido-mvp-brief.md. Key corrections for builders: `gbrain_min_version` 3/4-part (0.42 fails, use 0.42.0); `primitive` is closed 5-enum; pack `frontmatter_links` `{page_type,fields,link_type}` has NO inverse and NO direction (edge always declaring→referenced, reverse via backlinks); doctor needs BOTH `routing-eval.jsonl` (≥5) AND `evals/*.judge.json` (≥3); `type:` frontmatter beats slug prefix; `sync --apply` defaults to DRY-RUN (must pass --apply); CyclePhase is a closed 22-member union → 509 must be a skill. Edge-direction checkpoint: `gbrain graph engagements/<slug> --depth 1` + `gbrain backlinks clients/<slug>`.

## Ticket log (mirrors the tracker, kept terse)
- BLU-508: DONE  (wave 1, opus, authoring, has-new-ui: false)
  gates: validate→green, lint --with-db→green, use→active, sync --apply→green (would_apply=0, prefixes dead until 510 enriches — expected), explain→green
  files: packs/dido-engagement/dido-engagement.yaml (pack source), packs/dido-engagement/README.md (runbook), docs/adr/ADR-001-dido-engagement-ontology.md
  reused: gbrain-base (extends); brief's confirmed manifest shape
  net-new: hand-authored pack.yaml (fork output had wrong extends:null shape); `meeting` redeclared locally (lint validates frontmatter_links.page_type against on-disk child manifest, not extends-merged set)
  decisions: ADR-001 (expert_in originates on stakeholder not person — person is non-routed/inert; documented deviation)
  tests: n/a — gates (all 5 green, exit 0)
  NOTES FOR 510: frontmatter fields to stamp — engagement `client:`; deliverable/decision/risk/meeting `engagement:`; decision `requested_by:`/`approved_by:`; deliverable `requested_by:`; `depends_on:`; `blocked_by:`; stakeholder `expert_in:`; opportunity `renewal_for:`/`expansion_for:`. File stakeholders under `people/stakeholders/` OR stamp `type: stakeholder` (type frontmatter beats prefix; base `person` is a superset prefix). Edge-direction proof: file `engagements/<slug>` with `client: clients/<slug>`, then `gbrain graph engagements/<slug> --depth 1` shows `engagement --client_of--> client`; `gbrain backlinks clients/<slug>` lists the engagement. `gbrain schema review-orphans` errors (`relation "pages" does not exist`) in this pglite brain — experimental, NOT a gate; use `gbrain stats`.
- BLU-510: DONE  (wave 2, opus, authoring, has-new-ui: false)
  gates (GBRAIN_HOME=$HOME/.gbrain-dido, source abstudios-seed): all 5 green.
    1 enrich run → typed pages: client 1, engagement 1, meeting 5, decision 2, risk 1, opportunity 1, stakeholder 2, person 2, note +2 (cowork).
    2 graph engagements/abstudios-sierra --depth 1 → engagement --client_of--> clients/abstudios (DIRECTION PROVEN) + --blocked_by--> risk.
    3 backlinks clients/abstudios → engagement (client_of) + opportunity (expansion_for).
    4 engagement frontmatter `status: open`; opportunity `status: open`.
    5 cowork note lands as `note`, engagement link DEFERRED + queued in reports/enrich-open-questions.md.
  KEY FINDING: gbrain 0.42.53.0 does NOT auto-materialize custom-pack frontmatter_links — extractFrontmatterLinks walks the hardcoded base FRONTMATTER_LINK_MAP (base verbs only); frontmatterLinkTypeFromPack is exported but never called. So dido verbs (client_of/owned_by/context_for/requested_by/approved_by/depends_on/blocked_by/expert_in/renewal_for/expansion_for) need explicit `gbrain link <from> <to> --link-type <verb>`. Frontmatter is still stamped as the declarative contract (509 input + forward-compat). `attended` IS a base verb → auto-links from meeting attendees:/body refs (confirmed). This corrects ADR-001's "edges materialize from frontmatter_links" premise; see ADR-002.
  files: packs/dido-engagement/enrich/SKILL.md, packs/dido-engagement/enrich/filing-rules.md, docs/specs/dido-mvp-BLU-510-enrich-filing.md, docs/adr/ADR-002-enrich-filing-inference.md, reports/enrich-open-questions.md
  reused: dido-engagement pack (508); gbrain put/link/graph/backlinks; base attended auto-link; ask-user pattern; _brain-filing-rules.md
  decisions: ADR-002 (infer-first + ask-when-stuck, no numeric gate, rationale-note git-diff auditability, status:open = 509 contract, explicit-gbrain-link edge materialization, enrich-vs-512 dedupe)
  NOTES FOR 509: read `status: open` from engagements/abstudios-sierra and opportunities/florida-district (both stamped). Enumerate engagements/opportunities then read frontmatter status (filter path still TBD per plan — query/search --types). client.status is 509's to derive.
  NOTES FOR 511/512/513: typed slugs available to query on the validation brain — clients/abstudios, engagements/abstudios-sierra, meetings/2025-{03-12,04-02,07-14,08-08,10-03}-abstudios-sierra, decisions/2025-03-12-scheduling-separate-tab, decisions/2025-07-14-default-ai-model, risks/billing-cost-overrun, opportunities/florida-district, people/stakeholders/{scott-wayman,andrew-willett}, people/{ryan-ramirez,guilherme-garibaldi}. To materialize any new pack edge, stamp frontmatter AND `gbrain link` the verb (see packs/dido-engagement/enrich/filing-rules.md).
- BLU-509: TODO  (wave 3, opus, authoring, has-new-ui: false)
- BLU-511: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-512: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-513: TODO  (wave 4, opus, authoring, has-new-ui: false)
- BLU-519: TODO  (wave 5, opus, authoring, has-new-ui: false) — targets SHARED brain, no GBRAIN_HOME

## Open questions / escalations
- (none)
