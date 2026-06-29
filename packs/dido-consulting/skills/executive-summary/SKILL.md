---
name: dido-executive-summary
description: |
  On-demand leadership brief on one engagement (or a client's open engagement):
  Situation, Progress, Risks & blockers, Outlook / next steps. Tight,
  jargon-free, read-only, every claim cited to a source slug. Missing data is
  gap-flagged, never invented.
triggers:
  - "executive summary"
  - "exec summary"
  - "executive summary of this engagement"
  - "summarize this engagement for leadership"
  - "leadership summary"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Executive Summary

A short leadership brief on one engagement. Read-only. Four sections, plain
language, cited. Gap-flag what the brain does not hold.

## Read path

Traverse materialized edges (`gbrain backlinks` / `gbrain graph`), not raw
frontmatter (ADR-004).

1. **Resolve the engagement.** If the user names an engagement, use it. If they
   name a client, find the client's open engagement via `gbrain backlinks
   clients/<slug>` (`client_of`, the one with `status: open`). If it does not
   resolve to a single engagement, ask; do not guess.
2. **Engagement page.** `gbrain get engagements/<slug>` for `status:`,
   `owner:` (lead), `client:`, and the body (the situation).
3. **Children.** `gbrain backlinks engagements/<slug>` and `gbrain graph
   engagements/<slug> --depth 1`:
   - `owned_by` rows → `gbrain get` each and bucket by `type:`: decisions and
     deliverables feed Progress; risks feed Risks & blockers.
   - `blocked_by` (from graph) → blocking risks.
   - `context_for` meetings, newest `date:` first → recency and next steps.
   - Milestones / deliverables: if deliverable pages carry a `status:` or due
     date, use it for Outlook; if none exist, gap-flag.

## Output

```
# Executive summary — <Engagement Title>  [engagements/<slug>]

**Situation.** <1-2 sentences: what the engagement is and its state>  [engagements/<slug>, clients/<slug>]

**Progress.** <key decisions made and deliverables shipped, newest first>  [decisions/<slug>, deliverables/<slug>]

**Risks & blockers.** <open risks and what blocks the engagement; "none recorded" if empty>  [risks/<slug>]

**Outlook / next steps.** <next milestone or next touchpoint; gap-flag if none recorded>  [meetings/<date>-<slug>]
```

Keep it to a few lines per section. No jargon. Every line carries a slug.

## Anti-patterns

- Padding length. Leadership wants the four sections tight.
- Inventing a milestone, a due date, or a risk. Gap-flag.
- Summarizing the wrong engagement when the subject is ambiguous. Ask.
- Writing any page. Read-only.
