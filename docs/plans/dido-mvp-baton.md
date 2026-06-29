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
- BLU-509: DONE  (wave 3, opus, authoring, has-new-ui: false)
  gates: all 4 green. (1) derive → clients/abstudios `status: Active` (engagement open). (2) flip engagement open→closed → Past; restored to open → Active. (3) `status_override: Past` → SKIPPED, override stands; removed → re-derives Active. (4) filter-by-status command confirmed (enumerate `gbrain list --type client` then read `status:` via `gbrain get` — no frontmatter predicate exists; query/search are semantic).
  files: packs/dido-engagement/lifecycle-status/SKILL.md (dido-client-lifecycle-status derivation skill), docs/adr/ADR-003-client-lifecycle-derivation.md
  reused: enrich SKILL.md shape; backlinks traversal; ADR-001/002 findings
  decisions: ADR-003 (precedence Active>Past>Prospect>Lost; status vs status_override; skill-not-dream-phase = closed CyclePhase union; enumerate-then-read filter)
  finalSeedState: abstudios = Active, no override, engagement abstudios-sierra restored to `status: open`, opportunity florida-district `status: open`. Known-good for 511/512/513.
  NOTES FOR 511: client lifecycle in `status:` frontmatter on client pages; values exactly Active|Past|Prospect|Lost or unset; `status_override:` is the effective status when present. Enumerate a client's engagements/opportunities via `gbrain backlinks clients/<slug>` (client_of=engagements, expansion_for/renewal_for=opportunities), NOT frontmatter walking. SLICE NOW PROVEN end-to-end (508→510→509); next slice proof = Client Brief (511) returns a cited answer.
- BLU-511: DONE  (wave 4, opus, authoring, has-new-ui: false) — scaffolds the dido-consulting skillpack
  gates: (1) `gbrain skillpack doctor packs/dido-consulting --quick` → ★ 10/10 [endorsed], all 5 core + 5 badges. (2) Client Brief slice proof: cited one-pager on ABStudios, gap-flags severity/touchpoints, invents nothing (SLICE PROVEN end-to-end 508→510→509→511). (3) Weekly Account Health wrote reports/weekly-account-health/2026-06-29.md; Executive Summary returned 4 cited sections.
  files: packs/dido-consulting/** (skillpack.json, LICENSE, CHANGELOG.md, README.md, runbooks/bootstrap.md, evals/dido-consulting.judge.json (3 cases), test/+e2e/ stubs, skills/{client-brief,weekly-account-health,executive-summary}/{SKILL.md,routing-eval.jsonl}), docs/specs/dido-mvp-BLU-511-account-status-skills.md, docs/adr/ADR-004-dido-consulting-skillpack.md, reports/weekly-account-health/2026-06-29.md
  decisions: ADR-004 (skillpack layout from reference; doctor needs BOTH routing-eval.jsonl ≥5 AND evals/*.judge.json ≥3; MECE trigger namespaces partitioned across 511/512/513; skills traverse via backlinks not frontmatter_links)
  MECE TRIGGER MAP (512/513 MUST draw only from their reserved space — any exact phrase shared with 511 fails the WHOLE pack):
    511 TAKEN: client-brief = {client brief, brief me on this client, what's the state of this client, catch me up on this client, where are we with this client}; weekly-account-health = {account health, weekly account health, how are our accounts, account health digest, account health report}; executive-summary = {executive summary, exec summary, executive summary of this engagement, summarize this engagement for leadership, leadership summary}
    512 RESERVED: {log, record, track, list, what} × {decision, risk, deliverable}
    513 RESERVED: who-knows/expert/expertise space (who knows about, find an expert on, who's our expert on, expertise map, who should I ask about) + growth (opportunities, find opportunities, renewals coming up, expansion opportunities, where can we grow) + reuse (find a deliverable, have we made a X before, reuse a deck/memo, similar deliverables to X) + proposal (draft a proposal, proposal for this client, write a proposal)
  NOTES FOR 512/513 (keep doctor 10/10): add skill at packs/dido-consulting/skills/<name>/{SKILL.md, routing-eval.jsonl ≥5 intents}; register in skillpack.json under BOTH `skills` and `routing_evals`; bump CHANGELOG.md + skillpack.json `version` together; keep evals/*.judge.json ≥3 cases; re-run `gbrain skillpack doctor packs/dido-consulting --quick` after edits (must stay 10/10). Read-path: traverse gbrain backlinks/graph, read state from `status:` frontmatter; stakeholders via meeting `attendees:` + decision `requested_by:`/`approved_by:` (no direct stakeholder→client edge).
- BLU-512: DONE  (wave 4, opus, authoring, has-new-ui: false) — extends dido-consulting to 6 skills, v0.2.0
  gates: (1) doctor → ★ 10/10 [endorsed] with 6 skills (MECE triggers confirmed). (2) Meeting Prep + Risk Review cited, gap-flag missing data; Risk Review dedupes billing signal vs existing risk, proposes a migration-risk candidate without creating it. (3) Decision Log capture UPDATED existing decisions/2025-07-14-default-ai-model (no duplicate; dedupe by engagement+title/date), put returned auto_links=0 (confirms no frontmatter auto-materialize), explicit `gbrain link ... --link-type approved_by` → graph shows new --approved_by--> people/ryan-ramirez edge.
  files: packs/dido-consulting/skills/{meeting-prep,risk-review,decision-log}/{SKILL.md,routing-eval.jsonl}, skillpack.json (6 skills/6 routing_evals, v0.1.0→0.2.0), CHANGELOG.md (## [0.2.0]), evals/dido-consulting.judge.json (+3 = 6 cases), README.md
  decisions: none — covered by ADR-002 (dedupe boundary + explicit-link-on-write + infer-first)
  finalSeedState: decisions/2025-07-14-default-ai-model updated (Alternatives/Outcome=TBD + approved_by edge); ZERO pages added; all seed pages coherent for 513.
  NOTES FOR 513: skillpack.json now 6 skills/6 routing_evals, CHANGELOG/version 0.2.0, judge 6 cases. 18 trigger phrases taken (meeting-prep/risk-review/decision-log) — 513 must stay MECE-unique. decision-log is first mutating skill; write paths must `gbrain link` after `gbrain put` (auto_links=0 reproduced).
- BLU-513: DONE  (wave 4, opus, authoring, has-new-ui: false) — pack now 10 skills, v0.3.0
  gates: (1) doctor → ★ 10/10 [endorsed], 10 skills, MECE triggers. (2) Opportunity Finder surfaces opportunities/florida-district (expansion, abstudios), cited. Expertise Mapper wraps real `gbrain whoknows scheduling` → Scott Wayman 0.306, Andrew Willett 0.287, shaped with WHY + gap-flags thin expertise coverage. Deliverable Reuse gap-flags (no deliverable pages) without surfacing a note as a deliverable. Proposal Writer drafts grounded in decisions, marked DRAFT, gap-flags missing prior deliverables.
  files: packs/dido-consulting/skills/{opportunity-finder,proposal-writer,deliverable-reuse,expertise-mapper}/{SKILL.md,routing-eval.jsonl}, skillpack.json (10 skills/10 routing_evals, v0.2.0→0.3.0), CHANGELOG.md (## [0.3.0]), evals/dido-consulting.judge.json (+4 = 10 cases)
  decisions: none — covered by ADR-001 (expert_routing scope) + ADR-004 (skillpack read-path)
  finalSeedState: unchanged — 24 pages, read-only skills wrote nothing.
  NOTE FOR 519: read skills point at materialized backlinks + whoknows; they light up further once the shared brain carries real deliverable/expertise/opportunity pages.
- BLU-519: TODO  (wave 5, opus, authoring, has-new-ui: false) — targets SHARED brain, no GBRAIN_HOME

## Open questions / escalations
- (none)
