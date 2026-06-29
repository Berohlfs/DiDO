---
name: dido-opportunity-finder
description: |
  On-demand or scheduled scan of growth opportunities across the brain:
  renewals coming up (client, timing, status), expansions (client, rationale),
  and new opportunity signals inferred from recent activity (flagged for
  confirmation). Read-only. Every line cites its source slug. Missing data is
  gap-flagged, never invented.
triggers:
  - "opportunities"
  - "find opportunities"
  - "renewals coming up"
  - "expansion opportunities"
  - "where can we grow"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Opportunity Finder

Surface where Sierra can grow: recorded renewal and expansion opportunities,
plus candidate new opportunities inferred from recent activity. Read-only: this
skill proposes, it never writes an opportunity page (enrich and the human own
creation; ADR-002). Cite the source slug on every line. Gap-flag what the brain
does not hold; invent nothing.

## Read path (backlinks, not frontmatter walk)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` at filing time (ADR-002,
ADR-004). Traverse the materialized edges.

1. **Recorded opportunities.** `gbrain list --type opportunity`. `gbrain get`
   each. Read `status:` (open | won | lost) and the link to its client —
   `expansion_for: clients/<slug>` is an expansion, `renewal_for: clients/<slug>`
   is a renewal. Read the rationale and timing from the body / `## Provenance`.
2. **Confirm the client edge from the other side.** For a client in scope (the
   user may name one; otherwise scan all `clients/<slug>`), `gbrain backlinks
   clients/<slug>` returns `expansion_for` / `renewal_for` rows pointing at the
   opportunity. Use this to attach each opportunity to its client and to read the
   client's `status:` (Active | Past | Prospect | Lost) for context.
3. **Bucket.** Renewals = `renewal_for` opportunities (client, timing, status).
   Expansions = `expansion_for` opportunities (client, rationale, status). Read
   timing from the page; if no timing is recorded, gap-flag it rather than
   guessing a date.
4. **New signals from recent activity.** For each open engagement (`gbrain
   backlinks clients/<slug>` `client_of`, `status: open`), scan its `context_for`
   meetings newest `date:` first for growth language: a new region/market, a new
   product line, an upsell ask, a referral, budget headroom. A signal already
   covered by a recorded opportunity is NOT a new candidate (dedupe against
   step 1 by client + subject; e.g. the Florida-standards thread maps to the
   existing `opportunities/florida-district`). Propose each genuinely new signal
   as a candidate with rationale and the meeting slug it came from, flagged for
   confirmation. Do not write an opportunity page.

## Output

```
# Opportunity scan  [generated <date>]

## Renewals
- <Client> — timing: <when | not recorded>; status: <open|won|lost>  [opportunities/<slug>, clients/<slug>]
- _none recorded_

## Expansions
- <Client> — rationale: <why>; status: <open|won|lost>  [opportunities/<slug>, clients/<slug>]

## New opportunity signals (proposed — confirm before filing)
- <one-line signal> — client: <Client>; rationale: <why>; source: [meetings/<date>-<slug>]
- _none detected in recent activity_  [meetings/<date>-<slug>]
```

## Anti-patterns

- Inventing a renewal date or timing the page does not carry. Gap-flag.
- Proposing a candidate that duplicates a recorded opportunity (e.g.
  re-proposing the Florida-district expansion). Dedupe against the recorded set.
- Silently creating an opportunity page. This skill proposes; it never writes.
- A signal with no cited source meeting/session.
- Walking frontmatter to enumerate opportunities. The edge set comes from
  `gbrain list` + `gbrain backlinks`.
