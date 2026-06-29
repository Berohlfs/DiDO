# DiDO filing rules and provenance conventions (BLU-510)

Companion to `SKILL.md`. The exact rules the enrich step follows when filing a raw
artifact under the `dido-engagement` ontology. Read gbrain's
`skills/_brain-filing-rules.md` first; this layers the engagement domain on top.

## Slug and directory map

| Type | Prefix | Slug shape |
| -- | -- | -- |
| client | `clients/` | `clients/<org>` |
| engagement | `engagements/` | `engagements/<client>-<who>` or `engagements/<name>` |
| meeting | `meetings/` | `meetings/<YYYY-MM-DD>-<slug>` |
| decision | `decisions/` | `decisions/<YYYY-MM-DD>-<slug>` |
| risk | `risks/` | `risks/<slug>` |
| opportunity | `opportunities/` | `opportunities/<slug>` |
| deliverable | `deliverables/` | `deliverables/<slug>` |
| stakeholder | `people/stakeholders/` | `people/stakeholders/<slug>` |
| person (attendee) | `people/` | `people/<slug>` |

Type comes from `type:` frontmatter (wins) or the slug prefix. The enrich step
stamps both so a page never mis-resolves.

## Frontmatter fields the pack reads (stamp these exactly)

These field names must match the `dido-engagement` pack verbatim or no edge
materializes. Source: ADR-001 / BLU-508 handoff.

- engagement: `client: clients/<slug>`, `status: open|closed`, `owner: people/<slug>`
- meeting: `engagement: engagements/<slug>`, `attendees: [people/<slug>, ...]`, `owner:`
- deliverable / decision / risk: `engagement: engagements/<slug>`
- decision / deliverable: `requested_by: people/<slug>`
- decision: `approved_by: people/<slug>`
- deliverable / decision: `depends_on: <slug>`
- engagement / deliverable / decision: `blocked_by: risks/<slug>`
- stakeholder: `expert_in: expertise/<slug>`
- opportunity: `renewal_for:` / `expansion_for: clients/<slug>`, `status: open|won|lost`

## Status stamping (BLU-509's contract)

A newly created engagement is stamped `status: open`. A newly created opportunity
is stamped `status: open`. These two frontmatter fields are BLU-509's only inputs;
do not omit them. `client.status` is derived by BLU-509, not stamped here.

## Provenance

- Server-stamped on ingest and preserved through `put_page` write-through:
  `source_kind`, `source_uri`, `ingested_via`, `ingested_at`. The enrich step does
  not hand-set these.
- Human-readable rationale lives in a `## Provenance` section: one line per
  inferred link, dated `[enrich <date>]`. Deferred links get a `DEFERRED` line.
  Pages write through to the source git repo, so every inference is auditable in
  `git diff`.

## Edge materialization (build-specific)

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links` (the
extractor uses the hardcoded base map; the pack resolver is dormant). After
`gbrain put`, materialize each edge explicitly:

```
gbrain link <declaring> <referenced> --link-type <verb> --context "frontmatter.<field>: <value>"
```

`attended` is the exception (base verb, auto-links from `attendees:` / body
`[Name](people/<slug>)`). When a future gbrain build wires the pack resolver, the
frontmatter alone will suffice and these explicit calls become redundant, not
wrong.

## Dedupe vs BLU-512

Key: `engagement + title/date`. Enrich creates/updates; the 512 skill annotates an
existing page. Never two pages for one decision/risk/deliverable.
