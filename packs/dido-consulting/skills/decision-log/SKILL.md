---
name: dido-decision-log
description: |
  Dual-mode decision log. Capture: record a decision as a typed page (what was
  decided, rationale, alternatives, requested_by/approved_by + engagement, date,
  outcome TBD), cited to its meeting/session, then materialize its edges with
  gbrain link. Query: the chronological decision trail for an engagement or
  topic, with rationale and citations. Capture dedupes against an existing
  decision (enrich or prior) by engagement + title/date and updates rather than
  duplicating.
triggers:
  - "log this decision"
  - "record this decision"
  - "decision log"
  - "what did we decide about this"
  - "why did we decide this"
  - "decision history for this engagement"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
  - put_page
  - link
mutating: true
---

# DiDO Decision Log

Two modes off one skill. **Capture** (mutating) writes/updates a `decision`
page and materializes its edges. **Query** (read-only) returns the decision
trail. Pick the mode from the request: "log/record this decision" → capture;
"what/why did we decide", "decision history" → query.

## Why explicit link-on-write (load-bearing)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`
(ADR-002, ADR-004). Stamping `engagement:` / `requested_by:` / `approved_by:`
on a decision materializes NO edge on its own. Capture must therefore `gbrain
link` each edge explicitly after the `put`, or the decision is invisible to the
backlinks/graph read paths every other skill depends on.

## Capture mode (mutating)

1. **Resolve the engagement and source.** Engagement as in the read skills
   (`gbrain backlinks clients/<slug>` → open `client_of`). Identify the
   meeting/session the decision was made in for the citation. If the engagement
   does not resolve to one page, ask; do not guess.
2. **Dedupe FIRST (engagement + title/date).** `gbrain backlinks
   engagements/<slug>` `owned_by` rows of `type: decision`. If one matches this
   decision by title or date (e.g. enrich already filed
   `decisions/2025-03-12-scheduling-separate-tab` or
   `decisions/2025-07-14-default-ai-model`), UPDATE that page — annotate
   rationale / alternatives / outcome, do not create a second page. Only when no
   existing decision matches do you create a new `decisions/<YYYY-MM-DD>-<slug>`.
3. **Write the page.** `gbrain put decisions/<YYYY-MM-DD>-<slug>` with
   frontmatter `type: decision`, `engagement: engagements/<slug>`, `date:`,
   `requested_by: people/<slug>` and/or `approved_by: people/<slug>` when known,
   and a body: **what was decided**, **rationale (why)**, **alternatives
   considered**, **outcome: TBD**, cited to the meeting/session. Add a
   `## Provenance` line dated `[decision-log <date>]`.
4. **Materialize the edges (REQUIRED).** Frontmatter alone links nothing here:
   ```
   gbrain link decisions/<slug> engagements/<slug> --link-type owned_by --context "frontmatter.engagement"
   gbrain link decisions/<slug> people/<slug>      --link-type requested_by --context "frontmatter.requested_by"
   gbrain link decisions/<slug> people/<slug>      --link-type approved_by  --context "frontmatter.approved_by"
   ```
   Emit only the edges whose frontmatter fields are set. Verify with `gbrain
   graph decisions/<slug> --depth 1` (or `gbrain backlinks engagements/<slug>`).
5. **Report** the slug, whether it was a create or a dedupe-update, and the
   materialized edges.

## Query mode (read-only)

1. Resolve the engagement (or topic).
2. `gbrain backlinks engagements/<slug>` `owned_by` rows of `type: decision`;
   `gbrain get` each. For a topic, filter by title/body match.
3. Order by `date:` and render the trail, each with its rationale and slug.

```
# Decision history — <Engagement Title>  [engagements/<slug>]
- <date> <Title> — <rationale one line>; requested_by: <people/<slug> | n/r>; outcome: <value | TBD>  [decisions/<date>-<slug>]
```

## Anti-patterns

- Creating a second page for a decision that already exists. Dedupe by
  engagement + title/date and update instead.
- `put` without the `gbrain link` calls — the decision would not materialize on
  the read paths (this build does not auto-link pack frontmatter).
- Inventing an approver, a requester, or an outcome. Leave `requested_by` /
  `approved_by` unset when unknown and stamp `outcome: TBD`.
- A captured or recalled decision with no cited meeting/session.
