# dido-consulting

Read-only account-and-status skills for Sierra Studio's consulting brain. The
pack reads the `dido-engagement` ontology and produces grounded, cited reports.
It never invents data; missing data is gap-flagged.

## Skills

| Skill | Mode | Output |
|---|---|---|
| `client-brief` | on-demand | one-page brief on a single client |
| `weekly-account-health` | scheduled / on-demand | a dated report saved under `reports/weekly-account-health/` |
| `executive-summary` | on-demand | a tight leadership brief on one engagement |

## Read-path note (load-bearing)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`. The
`dido-engagement` edges (`client_of`, `owned_by`, `context_for`,
`expansion_for`, `renewal_for`) are materialized explicitly with `gbrain link`
at filing time (BLU-510, ADR-002). These skills therefore enumerate a client's
engagements / opportunities / risks / decisions / meetings through
`gbrain backlinks` and `gbrain graph`, not by walking frontmatter. See ADR-004.

Stakeholders are reached through meeting `attendees:` frontmatter and decision
`requested_by:` / `approved_by:`, since stakeholder pages carry no direct edge
to the client.

## Verification posture

Authoring, not unit tests. The gates are `gbrain skillpack doctor
dido-consulting --quick` (green) and a grounded, cited skill answer against the
seed. The `test/` and `e2e/` files are presence stubs for the doctor badges,
not the verification.

## Layout

```
skillpack.json
LICENSE  CHANGELOG.md  README.md  .gitignore
runbooks/bootstrap.md
evals/dido-consulting.judge.json
test/example.test.ts
e2e/example.e2e.test.ts
skills/client-brief/{SKILL.md,routing-eval.jsonl}
skills/weekly-account-health/{SKILL.md,routing-eval.jsonl}
skills/executive-summary/{SKILL.md,routing-eval.jsonl}
```
