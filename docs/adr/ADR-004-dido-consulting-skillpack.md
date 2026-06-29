# ADR-004: the dido-consulting skillpack — packaging and read-path

Status: Accepted
Date: 2026-06-29
Ticket: BLU-511 (scaffolds the pack that BLU-512 and BLU-513 extend)

## Context

The MVP read layer is three reporting skills — Client Brief, Weekly Account
Health, Executive Summary — over the `dido-engagement` ontology. They ship as
one publishable skillpack, `dido-consulting`, because BLU-512 (on-demand
decision/risk/deliverable skills) and BLU-513 (expertise mapper) add more skills
to the same pack. The packaging contract therefore has to be right once, and the
trigger namespace has to be reserved across all three tickets so a later skill
does not collide with an earlier one and fail `doctor`.

Two forces shaped this:

1. **Doctor is the verification gate, and it is specific.** `gbrain skillpack
   doctor` scores ten binary dimensions. Five are core; all five plus all five
   badges are required for the endorsed tier. Two requirements are easy to miss:
   each skill needs its own `routing-eval.jsonl` with ≥5 intents, AND the pack
   needs a `*.judge.json` under `evals/` with ≥3 cases. The reference pack ships
   BOTH shapes; they are not alternatives. Trigger phrases must be unique across
   the whole pack (MECE), checked by exact, case-insensitive equality.
2. **Custom-pack `frontmatter_links` do not auto-materialize in gbrain
   0.42.53.0** (ADR-002). The dido edges (`client_of`, `owned_by`,
   `context_for`, `expansion_for`, `renewal_for`) are created explicitly with
   `gbrain link` at filing time. So a read skill cannot trust raw frontmatter to
   enumerate a client's engagements or an engagement's children; it must read
   the materialized edge set.

Verification posture is authoring: doctor green plus a grounded, cited skill
answer against the seed, not unit tests.

## Decision

### Layout cloned from the reference

`packs/dido-consulting/` mirrors `gbrain/examples/skillpack-reference/`:
`skillpack.json`, `LICENSE`, `CHANGELOG.md`, `README.md`, `.gitignore`,
`runbooks/bootstrap.md`, `evals/dido-consulting.judge.json`, `test/` and `e2e/`
presence stubs, and per-skill `skills/<name>/SKILL.md` + `routing-eval.jsonl`.
The manifest's `version` (0.1.0) matches the CHANGELOG `## [0.1.0]` header.

`gbrain skillpack init dido-consulting` scaffolds a single-skill tree into the
working directory; the canonical source lives in the repo at
`packs/dido-consulting/`, and `doctor` finds it by being pointed at that path
(`gbrain skillpack doctor packs/dido-consulting --quick`). The pack is not
copied into a separate `skills/` workspace dir — the repo path is the source of
truth, and doctor takes an explicit `<pack-dir>`.

### Dual eval requirement: routing-eval AND judge.json

Each skill ships `skills/<name>/routing-eval.jsonl` with ≥5 `{intent,
expected_skill}` lines (satisfies core dim 3, `routing_evals_present`). The pack
ships one `evals/dido-consulting.judge.json` with three cases — happy path, an
empty-section edge case, an ambiguous-subject failure mode (satisfies badge dim
8, `llm_eval_present`). Both are required for endorsed; neither substitutes for
the other.

### MECE trigger namespace reserved across 511/512/513

Trigger phrases are partitioned by intent so future skills do not collide:

- **511 (taken):** brief/state/catch-up phrasings (client-brief); account-health
  phrasings (weekly-account-health); executive/exec/leadership-summary phrasings
  (executive-summary).
- **512 (reserved):** `{log, record, track, list, what}` × `{decision, risk,
  deliverable}`.
- **513 (reserved):** the who-knows / expert / expertise space.

511 deliberately avoids the verbs `log/record/track/list/who/expert`.

### Read-path: traverse backlinks, not frontmatter_links

Every skill enumerates related pages through `gbrain backlinks` and
`gbrain graph`, reading lifecycle/state off `status:` frontmatter on the target
pages. Stakeholders, which carry no direct edge to the client, are reached
through meeting `attendees:` frontmatter and decision
`requested_by:`/`approved_by:`; the engagement `owner:` is the lead. Skills are
read-only except Weekly Account Health, whose only write is its dated report
file (no brain page is mutated).

## Alternatives considered

- **One skill with sub-modes instead of three skills.** Rejected: doctor scores
  per-skill routing-evals and the three intents (brief / health digest / exec
  summary) route distinctly. Three skills keep routing clean and let 512/513
  extend the same pattern.
- **judge.json OR routing-eval, not both.** Rejected: the reference ships both
  and doctor scores them as separate dimensions (3 and 8). Shipping one drops a
  badge and the endorsed tier.
- **Walking `frontmatter_links` to enumerate relations.** Rejected for the same
  reason as ADR-002/003: the custom-pack resolver is dormant in 0.42.53.0, so
  the materialized backlink set is the only reliable enumeration. Frontmatter
  stays the declarative contract and the audit trail.
- **Reserving trigger phrases per-ticket only after collisions appear.**
  Rejected: doctor fails the whole pack on any shared phrase, so the namespace
  is reserved up front in this ADR and the spec.

## Consequences

- BLU-512 and BLU-513 add skills under `skills/<name>/` with a `SKILL.md` and a
  `routing-eval.jsonl` (≥5 intents), register them in `skillpack.json` `skills`
  and `routing_evals`, draw triggers only from their reserved namespace, and
  bump `CHANGELOG.md` + manifest `version` together. The single
  `evals/dido-consulting.judge.json` can grow cases or a sibling judge file can
  be added; either keeps badge 8.
- Re-run `gbrain skillpack doctor packs/dido-consulting --quick` after any skill
  is added; it must stay 10/10.
- The skills are only as fresh as the brain's materialized edges; if an edge was
  never created with `gbrain link`, the relation is invisible to the read-path
  (the same coupling ADR-002 introduced).
