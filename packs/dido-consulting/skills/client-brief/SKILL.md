---
name: dido-client-brief
description: |
  On-demand one-page brief on a single client: lifecycle status and lead, a
  snapshot of what moved recently, active engagements with their latest, key
  stakeholders, open risks, recent decisions, open questions/asks, and next
  touchpoints. Read-only. Every line cites its source slug. Missing data is
  gap-flagged, never invented.
triggers:
  - "client brief"
  - "brief me on this client"
  - "what's the state of this client"
  - "catch me up on this client"
  - "where are we with this client"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Client Brief

Produce a grounded one-page brief on one client. Read-only: this skill never
writes a page. Cite the source slug on every line. If a section has no data in
the brain, write a gap flag for it; do not invent.

## Read path (backlinks, not frontmatter walk)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` at filing time (ADR-002,
ADR-004). Traverse the materialized edges, not raw frontmatter.

1. **Resolve the client.** `gbrain list --type client` and match the user's
   name to a `clients/<slug>`. If no single match, stop and ask which client;
   do not guess.
2. **Client page.** `gbrain get clients/<slug>`. Read lifecycle from `status:`
   (values Active | Past | Prospect | Lost), or from `status_override:` if it
   is pinned. Read the title.
3. **Engagements and opportunities.** `gbrain backlinks clients/<slug>`:
   - `link_type: client_of` rows → engagements (`from_slug`).
   - `link_type: expansion_for` / `renewal_for` rows → opportunities.
4. **Per engagement.** `gbrain get engagements/<slug>` for `status:`
   (open | closed), `owner:` (the Sierra-side lead), and the body. Then
   `gbrain backlinks engagements/<slug>`:
   - `context_for` rows → meetings. Sort by the meeting `date:` to get the most
     recent; the latest meeting body is "what moved recently".
   - `owned_by` rows → decisions / risks / deliverables. `gbrain get` each and
     bucket by its `type:`.
   Also `gbrain graph engagements/<slug> --depth 1` to catch `blocked_by` risks
   (an engagement points at a risk it is blocked by).
5. **Stakeholders.** Stakeholder pages carry no direct edge to the client.
   Collect people slugs from the engagement's meetings' `attendees:` frontmatter
   and from decisions' `requested_by:` / `approved_by:`. Those under
   `people/stakeholders/` are client-side stakeholders (role/sponsor from the
   page body, `company:`, `expert_in:`). The engagement `owner:` (a `people/`
   slug on the Sierra side) is the lead.
6. **Open risks.** The `owned_by` risks plus any `blocked_by` risk from the
   graph. Read `severity:` if the page carries it; if not, gap-flag severity
   as not recorded.
7. **Recent decisions.** The `owned_by` decisions, newest `date:` first.
8. **Open questions / asks.** Read `reports/enrich-open-questions.md` for rows
   touching this client or its engagements (deferred links from enrich). If
   none, gap-flag.
9. **Next touchpoints.** If no future-dated meeting or scheduled touchpoint is
   recorded, gap-flag it. Do not invent a date.

## Output (one page)

```
# Client brief — <Title> (clients/<slug>)

**Lifecycle:** <status> · **Lead:** <people/<owner>>   [clients/<slug>, engagements/<slug>]

## Snapshot
- Active engagements: <n>  [engagements/<slug>...]
- Recently moved: <one line from the latest meeting>  [meetings/<date>-<slug>]

## Active engagements
- <Title> — status: <open|closed>; latest: <latest meeting line>  [engagements/<slug>, meetings/<date>-<slug>]

## Key stakeholders
- <Name> — <role>; sponsor: <yes|no>  [people/stakeholders/<slug>]

## Open risks
- <Title> — severity: <value | not recorded>  [risks/<slug>]

## Recent decisions
- <date> <Title>  [decisions/<date>-<slug>]

## Open questions / asks
- <question> | _none recorded_  [reports/enrich-open-questions.md]

## Next touchpoints
- <date / next step> | _no upcoming touchpoint recorded_
```

## Anti-patterns

- Inventing a value for an empty section. Gap-flag it.
- Walking frontmatter to enumerate engagements. In this build the edge set comes
  from `gbrain backlinks`.
- Treating an unresolved client name as a single match. Ask.
- Citing a claim with no source slug. Every line carries its slug.
- Writing any page. This skill is read-only.
