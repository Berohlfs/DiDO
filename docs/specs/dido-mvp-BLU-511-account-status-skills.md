# BLU-511: Account & status skills (the dido-consulting skillpack)

## Goal

Three read-only reporting skills over the `dido-engagement` ontology — Client
Brief, Weekly Account Health, Executive Summary — packaged as the
`dido-consulting` skillpack that BLU-512 and BLU-513 extend. The work is
non-obvious for two reasons: (a) every read-path must traverse materialized
backlinks rather than frontmatter, because gbrain 0.42.53.0 does not
auto-materialize custom-pack `frontmatter_links` (ADR-002/004); and (b) the
skillpack must pass `doctor` at the endorsed tier, which requires per-skill
`routing-eval.jsonl` AND a pack-level `*.judge.json`, plus trigger phrases that
are MECE-unique across the WHOLE pack including 512/513's future skills.

## Acceptance criteria

- [x] `gbrain skillpack doctor packs/dido-consulting --quick` is green
      (10/10, endorsed).
- [x] Pack ships the reference layout: `skillpack.json`, `LICENSE`,
      `CHANGELOG.md` (version matches manifest), `README.md`, `.gitignore`,
      `runbooks/bootstrap.md`, `evals/dido-consulting.judge.json` (≥3 cases),
      `test/` + `e2e/` presence stubs, and per-skill `SKILL.md` +
      `routing-eval.jsonl` (≥5 intents each).
- [x] Triggers are MECE-unique across the pack; namespaces are reserved for
      512/513 so they cannot collide.
- [x] Client Brief produces a grounded, cited one-page brief against the seed
      that gap-flags missing data and invents nothing (slice proof).
- [x] Weekly Account Health writes a cited report to
      `reports/weekly-account-health/<date>.md` and mutates no brain page.
- [x] Executive Summary returns a tight, cited four-section leadership brief.

## Behavior / edge cases

**Read-path (the load-bearing finding).** All three skills enumerate a client's
engagements / opportunities / risks / decisions / meetings through
`gbrain backlinks` and `gbrain graph`, never by walking frontmatter. The
materialized edges and how each skill reads them:

| From | Command | link_type | Means |
|---|---|---|---|
| client | `backlinks clients/<slug>` | `client_of` | engagement |
| client | `backlinks clients/<slug>` | `expansion_for` / `renewal_for` | opportunity |
| engagement | `backlinks engagements/<slug>` | `context_for` | meeting |
| engagement | `backlinks engagements/<slug>` | `owned_by` | decision / risk / deliverable (bucket by `type:`) |
| engagement | `graph engagements/<slug> --depth 1` | `blocked_by` | blocking risk (edge points engagement→risk) |

Lifecycle status is read off the `status:` frontmatter on the client page
(`Active|Past|Prospect|Lost`, or `status_override:` if pinned). Engagement state
is `status: open|closed`; opportunity state is `status: open|won|lost`.

**Stakeholders have no direct edge to the client.** Reach them through the
engagement's meetings' `attendees:` frontmatter and decisions'
`requested_by:` / `approved_by:`. People under `people/stakeholders/` are
client-side stakeholders; the engagement `owner:` (a `people/` slug) is the
Sierra-side lead. (Confirmed on the seed: `attended` backlinks on meetings are
partial — only body-linked attendees materialize — so `attendees:` frontmatter
is the reliable source, not the `attended` edge.)

**Gap-flagging, not invention.** Empty sections are flagged explicitly:
- Risk `severity:` is absent on the seed risk → "severity: not recorded".
- No future-dated meeting → "no upcoming touchpoint recorded".
- `reports/enrich-open-questions.md` rows are matched to the client/engagement;
  the seed's two OPEN rows are internal R&D (no engagement), so a client brief
  for ABStudios gap-flags Open questions as none-for-this-client rather than
  pulling unrelated rows.

**Weekly Account Health diff + write.** The skill reads the lexically greatest
prior report under `reports/weekly-account-health/` strictly before today and
diffs per client (status changes, new/cleared risks, engagement movement, new
opportunities). First run is a stated baseline. The only write is the report
file; no brain page is created or changed (`writes_pages: false`).

**Ambiguous subject.** If a client/engagement name does not resolve to a single
page, the skill asks for disambiguation instead of guessing (failure-mode case
in the judge eval).

## Output templates

Captured in each `SKILL.md` body under `## Output`. Client Brief is a one-pager
(Header · Snapshot · Active engagements · Key stakeholders · Open risks · Recent
decisions · Open questions/asks · Next touchpoints), every line cited. Weekly
Account Health is a dated report (Summary + per-active-client block). Executive
Summary is four sections (Situation · Progress · Risks & blockers · Outlook /
next steps).

## MECE trigger map (whole pack — reserve namespaces for 512/513)

Doctor's `skills_have_unique_triggers` checks exact phrase equality
(case-insensitive) across all skills in the pack. Phrases are partitioned by
intent namespace so 512/513 add skills without colliding.

**BLU-511 (this ticket) — TAKEN:**

| Skill | Trigger phrases |
|---|---|
| `client-brief` | `client brief` · `brief me on this client` · `what's the state of this client` · `catch me up on this client` · `where are we with this client` |
| `weekly-account-health` | `account health` · `weekly account health` · `how are our accounts` · `account health digest` · `account health report` |
| `executive-summary` | `executive summary` · `exec summary` · `executive summary of this engagement` · `summarize this engagement for leadership` · `leadership summary` |

**RESERVED — do not reuse in 511:**

- **BLU-512 (on-demand decision/risk/deliverable logging + listing):** the
  `{log, record, track, list, what}` × `{decision, risk, deliverable}` space,
  e.g. `log a decision`, `record a risk`, `track a deliverable`,
  `list decisions for this engagement`, `what risks on this engagement`.
- **BLU-513 (expertise mapper / whoknows):** the who-knows / expert / expertise
  space, e.g. `who knows about`, `find an expert on`, `who's our expert on`,
  `expertise map`, `who should I ask about`.

511 deliberately avoids the verbs `log/record/track/list/who/expert` so the
reserved namespaces stay clean.

## Doctor rubric checklist (10 binary dims; ★ = met)

Core (all 5 required): ★ `manifest_valid` · ★ `skills_have_skill_md`
(name+description+triggers) · ★ `routing_evals_present` (≥5 lines/skill) ·
★ `skills_have_unique_triggers` · ★ `changelog_present_and_current`
(`## [0.1.0]` matches manifest). Badges (all 5 met → endorsed):
★ `unit_tests_present` · ★ `e2e_tests_present` · ★ `llm_eval_present`
(`evals/*.judge.json` ≥3 cases) · ★ `bootstrap_runbook_present` ·
★ `license_present`.

## Test plan (per posture: authoring — gbrain validation gates)

1. `gbrain skillpack doctor packs/dido-consulting --quick` → 10/10 endorsed.
2. Client Brief against the ABStudios seed → cited one-page brief that
   gap-flags severity / next touchpoint / open questions and invents nothing
   (the 508→510→509→one-skill slice proof).
3. Weekly Account Health → writes `reports/weekly-account-health/2026-06-29.md`,
   cited, brain pages untouched.
4. Executive Summary on `engagements/abstudios-sierra` → four cited sections.

## Reuse & decisions

- Reuses: the `examples/skillpack-reference` layout (cloned shape), the
  `dido-engagement` SKILL.md frontmatter idiom (`name`/`description`/`triggers`
  /`tools`/`mutating`/`writes_to`), and the `gbrain backlinks`/`graph` read-path
  established by BLU-509/510 (ADR-002/003).
- Net-new: the `dido-consulting` skillpack itself — read-only reporting layer.
  The reference's single-skill scaffold did not fit a three-skill pack, so the
  manifest lists three skills and three routing-evals and the trigger space is
  partitioned MECE across 511/512/513.
- ADRs: ADR-004 (skillpack packaging + the backlinks read-path decision).
