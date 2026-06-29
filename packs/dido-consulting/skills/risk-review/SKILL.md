---
name: dido-risk-review
description: |
  On-demand or scheduled risk review for an engagement or client: per recorded
  risk — description, severity, status, owner, linked engagement, and latest
  update; then candidate NEW risks inferred from recent meetings/sessions,
  proposed with rationale and flagged for confirmation, never silently created.
  Read-only. Every line cites its source slug. Missing data is gap-flagged.
triggers:
  - "risk review"
  - "what are the risks on this engagement"
  - "review risks"
  - "any risks I should know about"
  - "risk review for this client"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Risk Review

Review the recorded risks on one engagement and propose candidate new risks from
recent activity. Read-only: this skill proposes, it never writes a risk page
(enrich and the human own creation; ADR-002). Cite the source slug on every
line. Gap-flag what the brain does not hold.

## Read path (backlinks, not frontmatter walk)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` (ADR-002, ADR-004). Traverse the
materialized edges.

1. **Resolve the engagement.** If the user names a client, find its open
   engagement via `gbrain backlinks clients/<slug>` (`client_of`,
   `status: open`). If the subject does not resolve to a single engagement, ask.
2. **Recorded risks.** `gbrain backlinks engagements/<slug>` `owned_by` rows of
   `type: risk`, plus `gbrain graph engagements/<slug> --depth 1` `blocked_by`
   rows (an engagement points at the risk that blocks it). `gbrain get` each.
   Read `severity:`, `status:`, `owner:`, the linked engagement, and the latest
   update from the body / `## Provenance`. When a field is absent (the seed risk
   carries no `severity:`/`status:`/`owner:`), gap-flag that field as not
   recorded — do not assign a value.
3. **Recent activity for emerging signals.** `context_for` meetings (and any
   sessions) newest `date:` first. Scan bodies for risk language: cost/billing
   exposure, scope slippage, schedule/migration risk, dependency or vendor risk,
   security. A signal already covered by a recorded risk is NOT a new candidate
   (dedupe against step 2 by subject + engagement; e.g. the billing-limits note
   maps to the existing `risks/billing-cost-overrun`).
4. **Infer-first, do not create.** For each genuinely new signal, propose a
   candidate risk with its rationale and the meeting slug it came from, flagged
   for confirmation. Do not write a risk page and do not duplicate one enrich
   already filed.

## Output

```
# Risk review — <Engagement Title>  [engagements/<slug>]

## Recorded risks
- <Title> — severity: <value | not recorded>; status: <value | not recorded>; owner: <people/<slug> | not recorded>; latest: <update line>  [risks/<slug>, engagements/<slug>]

## Candidate new risks (proposed — confirm before filing)
- <one-line risk> — rationale: <why>; source: [meetings/<date>-<slug>]
- _none detected in recent activity_  [meetings/<date>-<slug>]
```

## Anti-patterns

- Inventing a severity, status, or owner the page does not carry. Gap-flag.
- Proposing a candidate that duplicates a recorded risk (e.g. re-proposing
  billing-cost-overrun). Dedupe against the recorded set first.
- Silently creating a risk page. This skill proposes; it never writes.
- A candidate with no cited source meeting/session.
