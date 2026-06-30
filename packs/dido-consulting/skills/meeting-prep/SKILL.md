---
name: dido-meeting-prep
description: |
  On-demand prep for an upcoming client meeting: who's in the room (attendees
  and roles), where the engagement stands, open items to raise (pending
  decisions, risks, asks), a recap of the last meeting and its action-item
  status, and suggested talking points. Read-only. Every line cites its source
  slug. Missing data is gap-flagged, never invented.
triggers:
  - "meeting prep"
  - "prep me for this meeting"
  - "what do I need to know before this meeting"
  - "prep for my client call"
  - "prep me for this client"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Meeting Prep

Produce a grounded prep brief for an upcoming client meeting. Read-only: this
skill never writes a page. Cite the source slug on every line. Gap-flag any
section the brain does not hold; do not invent.

## Read path (backlinks, not frontmatter walk)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges are materialized with `gbrain link` at filing time (ADR-002,
ADR-004). Traverse the materialized edges, not raw frontmatter.

1. **Resolve the meeting and engagement.** If a calendar surfaces a specific
   upcoming meeting, use it. Otherwise prep against the engagement's most recent
   recorded meeting as the working subject and say so. Resolve the engagement:
   if the user names a client, find its open engagement via `gbrain backlinks
   clients/<slug>` (`client_of`, `status: open`); if the subject does not
   resolve to a single engagement, ask. Do not guess.
2. **Engagement state.** `gbrain get engagements/<slug>` for `status:`,
   `owner:` (the Sierra-side lead), `client:`, and the body.
3. **Meetings.** `gbrain backlinks engagements/<slug>` → `context_for` rows are
   the meetings. Sort by meeting `date:`. The newest recorded meeting is the
   "last meeting" for the recap; the upcoming meeting (calendar) is the subject.
4. **Who's in the room.** Attendees come from the meeting `attendees:`
   frontmatter (calendar invite if available; otherwise the last meeting's
   attendees as the expected room). For each `people/stakeholders/<slug>`,
   `gbrain get` for role/company from the body, `company:`, `expert_in:`. The
   engagement `owner:` (a `people/` slug) is the Sierra lead. Note when an
   attendee list is only inferred from the last meeting.
5. **Open items to raise.** `gbrain backlinks engagements/<slug>` `owned_by`
   rows plus `gbrain graph engagements/<slug> --depth 1` `blocked_by` rows.
   `gbrain get` each and bucket by `type:`: decisions still in motion, open
   risks, and open asks. Read `reports/enrich-open-questions.md` for asks
   touching this engagement. If a bucket is empty, gap-flag it.
6. **Last meeting recap + action items.** The newest `context_for` meeting body
   is the recap. Action items: items the meeting body records as to-do /
   follow-up. The seed meetings carry narrative bodies, not a structured
   action-item list — when no explicit action items are recorded, gap-flag the
   action-item status rather than inferring completion.
7. **Suggested talking points.** Synthesize from the above (open decisions,
   open risks, unresolved asks, last-meeting follow-ups). Each talking point
   carries the slug of the item it is drawn from; do not introduce a point with
   no cited basis.

## Output

```
# Meeting prep — <Engagement Title>  [engagements/<slug>]
Subject meeting: <upcoming date | last recorded meeting <date>, no calendar event found>

## Who's in the room
- <Name> — <role>; <company>  [people/stakeholders/<slug>]
- <Sierra lead Name> — Sierra lead  [people/<owner>]

## Where things stand
- Engagement status: <open|closed>; <one line of recent movement>  [engagements/<slug>, meetings/<date>-<slug>]

## Open items to raise
- Decision in motion: <Title>  [decisions/<date>-<slug>]
- Open risk: <Title>  [risks/<slug>]
- Ask: <question> | _none recorded_  [reports/enrich-open-questions.md]

## Last meeting recap (<date>)
- <recap line>  [meetings/<date>-<slug>]
- Action items: <status> | _no action items recorded_  [meetings/<date>-<slug>]

## Suggested talking points
- <point>  [<source slug>]
```

## Anti-patterns

- Inventing attendees, an agenda, or action-item completion. Gap-flag.
- Treating the last meeting's attendees as confirmed for the upcoming one
  without saying it is inferred.
- A talking point with no cited basis.
- Walking frontmatter to enumerate meetings or children. The edge set comes from
  `gbrain backlinks` / `gbrain graph`.
- Writing any page. This skill is read-only.
