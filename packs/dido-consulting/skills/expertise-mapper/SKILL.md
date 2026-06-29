---
name: dido-expertise-mapper
description: |
  On-demand expert routing: given a topic, return ranked people/expertise from
  the brain with the WHY behind each (recent work, linked engagements and
  deliverables). Thin wrapper over the built-in find_experts op (CLI
  `gbrain whoknows`). Read-only. Every line cites its source slug. When the brain
  holds thin expertise data the ranking is reported as-is and gap-flagged.
triggers:
  - "who knows about this"
  - "who has worked on this"
  - "find an expert on this"
  - "who's done this before"
  - "who should I ask about this"
tools:
  - whoknows
  - get_page
  - get_backlinks
  - graph
mutating: false
---

# DiDO Expertise Mapper

Route an expertise question to the right people. This skill shapes the query and
output around the first-class `find_experts` op (CLI `gbrain whoknows`); it does
not reimplement scoring. Read-only. Cite the source slug on every line. If the
op returns little, report it as-is and gap-flag — do not pad the list with
people who do not match (ADR-001 scopes `expert_routing` to stakeholder +
expertise + person; ADR-004 the skillpack read-path).

## Read path (whoknows is the engine)

1. **Extract the topic.** Reduce the request to a free-form topic string (e.g.
   "scheduling", "AI model selection"). If no topic is given, ask for one.
2. **Run the op.** `gbrain whoknows "<topic>" --explain`. It filters at SQL to
   person/company pages (stakeholder + person here) and ranks by expertise depth,
   relationship recency (6-month half-life decay), and salience. Take the ranked
   list as the spine of the answer — this skill does not re-rank.
3. **Add the WHY via backlinks.** For each returned person/stakeholder slug,
   establish why they rank: `gbrain get` the page for `expert_in:` / role, then
   traverse for recent work. A stakeholder carries no direct engagement edge, so
   reach their work through the engagement: `gbrain backlinks
   engagements/<slug>` `context_for` meetings whose `attendees:` include the
   person, and `owned_by` decisions whose `requested_by:` / `approved_by:` is the
   person, plus `owned_by` deliverables they produced (`context_for` traversal of
   `owned_by`/`context_for` per ADR-001). Cite the linking slug.
4. **Thin-seed reality.** The seed is thin on dedicated `expertise` pages, so
   whoknows may return only stakeholders with a low score. Still run the op,
   report the ranked candidates with their score, and gap-flag that expertise
   coverage is thin rather than inventing an expert. An empty result is a valid,
   gap-flagged answer — confirm the op ran.

## Output

```
# Who knows about "<topic>"  [via gbrain whoknows]

## Ranked candidates
1. <Name> — <role/expert_in>; score <n>
   why: <recent work>  [people/stakeholders/<slug>, meetings/<date>-<slug> | decisions/<slug>]
2. ...

_thin expertise coverage for "<topic>" — ranked on stakeholder match only_  [via gbrain whoknows]
_no candidates returned for "<topic>"_  [via gbrain whoknows]
```

## Anti-patterns

- Re-ranking or filtering away the op's results by hand. Shape, don't replace,
  `find_experts`.
- Naming an expert whom whoknows did not return. The op is the source of truth.
- A candidate with a "why" that cites no engagement/meeting/decision slug.
- Treating an empty/thin result as a failure. Run the op, report it, gap-flag.
