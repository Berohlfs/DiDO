---
name: dido-deliverable-reuse
description: |
  On-demand search for past deliverables and assets to reuse: given a topic or
  artifact type (deck, memo, plan, report), return a ranked list — title,
  client/engagement, date, what it is, why it's relevant, and a link. Read-only.
  Every line cites its source slug. When the brain holds no matching deliverable,
  that is gap-flagged, never invented.
triggers:
  - "find a deliverable"
  - "have we made this before"
  - "reuse a deck"
  - "similar deliverables to this"
  - "reuse a memo"
tools:
  - list
  - get_page
  - search
  - get_backlinks
mutating: false
---

# DiDO Deliverable Reuse

Find past deliverables and assets worth reusing for a new request. Read-only:
this skill never writes a page. Cite the source slug on every line. If the brain
holds no matching deliverable, gap-flag it; do not fabricate a result.

## Read path (search + backlinks)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` (ADR-002, ADR-004). Use search to
find candidates, then traverse materialized edges for provenance.

1. **Find candidates.** Run `gbrain search "<topic or artifact type>"` for the
   user's subject, and `gbrain list --type deliverable` to enumerate recorded
   deliverables directly. Keep deliverable/asset pages; drop unrelated note hits.
2. **Read each candidate.** `gbrain get deliverables/<slug>`. Read the title,
   `date:`, what the artifact is (body / type of asset), and its owning
   engagement. The engagement edge surfaces via `owned_by` — confirm with
   `gbrain backlinks engagements/<slug>` (`owned_by` rows of `type: deliverable`)
   or read the deliverable's own link to its engagement.
3. **Resolve client/engagement.** From the owning engagement, `gbrain get
   engagements/<slug>` for `client:`; `gbrain get clients/<slug>` for the client
   title. This is the "client/engagement" column.
4. **Rank by relevance.** Order by how closely the deliverable's subject and
   artifact type match the request, then by recency (`date:`). State the "why
   relevant" for each — same artifact type, same domain, same client, reusable
   structure.
5. **Thin-seed reality.** The seed is thin on `deliverable` pages; `gbrain list
   --type deliverable` may return nothing. When no deliverable matches, run the
   search anyway and report the gap explicitly with what was searched — do not
   surface a note or meeting as if it were a deliverable.

## Output

```
# Deliverable reuse — "<request>"

## Ranked matches
1. <Title> — <Client> / <Engagement>; <date>
   what: <one line>; why relevant: <reason>  [deliverables/<slug>, engagements/<slug>]
2. ...

_no matching deliverable in the brain for "<request>" — searched <terms>_  [searched: gbrain search]
```

## Anti-patterns

- Returning a note, meeting, or decision page as if it were a deliverable. Only
  `type: deliverable` / asset pages qualify.
- Inventing a deliverable that does not exist. Gap-flag an empty result.
- A match line with no link to its source slug or no client/engagement context.
- Claiming relevance without stating why (artifact type, domain, client).
