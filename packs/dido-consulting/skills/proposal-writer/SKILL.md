---
name: dido-proposal-writer
description: |
  On-demand proposal draft for a target client, grounded in past work:
  understanding/context, a proposed approach drawing on similar past
  engagements and deliverables (cited), relevant experience (linked
  deliverables/assets), scope & deliverables, and next steps. Read-only — drafts,
  never files. Every reused claim cites its source asset. Missing data is
  gap-flagged, never invented.
triggers:
  - "draft a proposal"
  - "proposal for this client"
  - "write a proposal"
  - "put together a proposal"
  - "draft a statement of work"
tools:
  - list
  - get_page
  - search
  - get_backlinks
  - whoknows
mutating: false
---

# DiDO Proposal Writer

Draft a proposal for a target client grounded in Sierra's past work. Read-only:
this skill produces a draft for a human to send; it never writes a page to the
brain. Every claim that reuses past work cites the source asset slug. Gap-flag
what the brain does not hold; do not invent capabilities, results, or scope.

## Read path (backlinks + search + whoknows)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` (ADR-002, ADR-004). Traverse the
materialized edges.

1. **Resolve the target.** `gbrain list --type client` and match the named
   client to `clients/<slug>`; if the proposal is for a prospect not yet in the
   brain, say so and draft from analogous past work. If a client name does not
   resolve to a single page, ask. `gbrain get clients/<slug>` for `status:`, and
   `gbrain backlinks clients/<slug>` (`client_of`) for any existing engagement.
2. **Understand the context.** From the target engagement (if any), `gbrain get
   engagements/<slug>` and its `context_for` meetings (newest first) for the
   stated need. For a prospect, take the need from the user's request and label
   it as such. This feeds "Understanding/context".
3. **Find similar past work.** `gbrain search "<problem/domain>"` plus `gbrain
   list --type deliverable` to surface deliverables and assets from other
   engagements that match the problem. `gbrain get` each; resolve its owning
   engagement/client via `owned_by` backlinks. These are the cited basis for the
   proposed approach and the "Relevant experience" list.
4. **Name the right people.** `gbrain whoknows "<problem/domain>"` to identify
   who has done this before; cite them as proposed staffing with their why
   (recent work via backlink traversal). This is suggestion, not commitment.
5. **Thin-seed reality.** The seed is thin on `deliverable`/`expertise` pages.
   When no analogous deliverable exists, draft the approach from the engagement
   record and recorded decisions (e.g. the AI-model-selection decision) and
   gap-flag that no prior deliverable was found to reuse — do not fabricate a
   case study. Every reuse claim must trace to a real cited slug.

## Output (draft — for a human to review and send)

```
# Proposal draft — <Client>  [clients/<slug>; DRAFT, not filed]

## Understanding & context
- <what the client needs and why>  [engagements/<slug>, meetings/<date>-<slug> | user request]

## Proposed approach
- <approach step, drawing on similar past work>  [deliverables/<slug> | decisions/<slug>]
- _no prior deliverable found to reuse for <X> — approach proposed from engagement record_  [searched: gbrain search]

## Relevant experience
- <Past work title> — <Client/Engagement>; <what it was>  [deliverables/<slug>, engagements/<slug>]

## Suggested team
- <Name> — <why: recent work>  [people/<slug>] (via gbrain whoknows)

## Scope & deliverables
- <deliverable / workstream>  [grounded in <slug> | newly proposed — confirm]

## Next steps
- <step>
```

## Anti-patterns

- Citing a case study, result, or capability not backed by a page in the brain.
  Gap-flag instead.
- Presenting a draft as filed. This skill drafts; it never writes to the brain.
- Reusing past work without citing the source asset slug.
- Inventing scope or staffing as committed. Newly proposed scope and suggested
  team are flagged for human confirmation.
