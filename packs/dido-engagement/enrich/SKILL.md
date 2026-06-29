---
name: dido-enrich-filing
description: |
  Capture, filing, and provenance for the dido-engagement ontology. Files a raw
  artifact (Fellow meeting transcript, Cowork session, note) as the right typed
  page, infers its client and engagement, stamps the frontmatter the pack reads,
  and materializes the typed edges. Infer first; ask only when stuck. Low
  confidence defers the uncertain link and queues a question; it never blocks
  filing.
triggers:
  - "file this artifact"
  - "enrich and file"
  - "ingest this transcript"
  - "capture this cowork session"
  - "what engagement does this belong to"
tools:
  - search
  - query
  - get_page
  - put_page
  - add_link
  - get_backlinks
mutating: true
writes_pages: true
writes_to:
  - clients/
  - engagements/
  - meetings/
  - decisions/
  - risks/
  - opportunities/
  - deliverables/
  - people/stakeholders/
---

# DiDO Enrich + Filing

Turn a raw artifact into the right typed page with provenance, filed and linked
automatically. Read `filing-rules.md` (next to this file) and gbrain's
`skills/_brain-filing-rules.md` before writing any page.

## Contract

- The artifact ALWAYS lands as a page. Filing is never blocked by low confidence.
- The page's type is set by `type:` frontmatter (which beats slug prefix,
  `markdown.ts:135`) and a matching slug prefix.
- The client and engagement are inferred from content and stamped. The engagement
  and client pages are created if absent.
- Every inferred link carries a one-line rationale note on the page.
- A new engagement is stamped `status: open`; a new opportunity `status: open`.
- An uninferable link defers: it is left unstamped, a deferral note is written on
  the page, and a question is appended to `reports/enrich-open-questions.md`.

## Type inference

1. If the artifact already declares `type:`, honor it.
2. Else infer from content and write `type:` explicitly:
   - a dated meeting/call transcript → `meeting` (`meetings/<date>-<slug>`)
   - a recurring client work thread → `engagement` (`engagements/<slug>`)
   - the client org itself → `client` (`clients/<slug>`)
   - a recorded choice with rationale → `decision` (`decisions/<date>-<slug>`)
   - a tracked threat/blocker → `risk` (`risks/<slug>`)
   - a potential new/expanded deal → `opportunity` (`opportunities/<slug>`)
   - a committed work product → `deliverable` (`deliverables/<slug>`)
   - an expert person on the engagement → `stakeholder`
     (`people/stakeholders/<slug>` or `type: stakeholder`)
3. When the type is genuinely unclear, file as `note` (the page still lands) and
   queue a typing question. Do not guess a domain type you are not confident in.

## Linkage inference (infer first)

Read the artifact, then infer and stamp these fields (the pack reads them):

| Page type | Stamp | Edge it declares |
| -- | -- | -- |
| engagement | `client: clients/<slug>` | `client_of` engagement → client |
| meeting | `engagement: engagements/<slug>` | `context_for` meeting → engagement |
| deliverable / decision / risk | `engagement: engagements/<slug>` | `owned_by` child → engagement |
| decision / deliverable | `requested_by: people/<slug>` | `requested_by` |
| decision | `approved_by: people/<slug>` | `approved_by` |
| deliverable / decision | `depends_on: <slug>` | `depends_on` |
| engagement / deliverable / decision | `blocked_by: risks/<slug>` | `blocked_by` |
| stakeholder | `expert_in: expertise/<slug>` | `expert_in` |
| opportunity | `renewal_for:` / `expansion_for: clients/<slug>` | `renewal_for` / `expansion_for` |

Also stamp `owner: people/<slug>` from the artifact/export context, and
`attendees:` on meetings from the transcript.

A meeting that names a client thread (recurring title, named client people)
infers `engagement:`. If the engagement page does not exist yet, create it first
(`status: open`, `client:` stamped, `client_of` materialized), then link the
meeting to it.

## Materializing edges (REQUIRED — read this)

Stamping the frontmatter is necessary but NOT sufficient in gbrain 0.42.53.0. The
frontmatter-link extractor walks the hardcoded base `FRONTMATTER_LINK_MAP`
(`link-extraction.ts`), which has only base verbs; the pack-aware resolver
`frontmatterLinkTypeFromPack` is never called, so the dido verbs do not
auto-materialize. For every edge in the table above, after `gbrain put`, create
the edge explicitly with the pack verb:

```
gbrain link <declaring-slug> <referenced-slug> --link-type <verb> \
  --context "frontmatter.<field>: <value>"
```

Direction is declaring-page → referenced-page, identical to what the frontmatter
declares. The reverse reading (an engagement's "owns" view) is a backlinks query,
never a second verb. `attended` is the one exception: it IS in the base map, so a
meeting's `attendees:` and body `[Name](people/<slug>)` references auto-link on
`put` — do not create those by hand.

## Rationale notes (auditability)

Every page that carries an inferred link gets a `## Provenance` section with one
line per inferred link:

```
## Provenance
- inferred `engagement: engagements/abstudios-sierra` — recurring "ABStudios / Sierra"
  client thread, client people named in transcript [enrich 2026-06-29]
```

Pages write through to the source repo, so a wrong inference shows up in
`git diff` and is cheap to fix. This is the safety net that lets the step infer
aggressively without a numeric confidence gate.

## Low confidence → ask (the deferral path)

When you cannot infer a link with confidence:

1. Write the page anyway (type stamped, body filed). The page lands.
2. Leave the uncertain field unstamped. Do not guess.
3. Add a deferral line to `## Provenance`:
   `- DEFERRED engagement link — no client named; queued (see reports/enrich-open-questions.md) [enrich 2026-06-29]`
4. Append a question to `reports/enrich-open-questions.md` (one row: artifact,
   the uncertain link, candidate answers, status `OPEN`).
5. When a human answers, stamp the field, materialize the edge with `gbrain link`,
   flip the rationale note, and mark the question `RESOLVED`.

Use gbrain's `ask-user` choice-gate pattern when a human is in the loop live; use
the open-questions file when running headless.

## Dedupe vs BLU-512

Enrich is the automatic page-creating path for decision/risk/deliverable pages.
BLU-512's skills are the on-demand path. Dedupe on `engagement + title/date`: if a
matching page exists, enrich updates it and the 512 skill annotates it. Do not
create a second page for the same decision.

## Anti-patterns

- Blocking the filing because a link is uncertain. The page always lands.
- Stamping frontmatter and assuming the edge exists. In this build it does not;
  run `gbrain link`.
- Guessing an engagement to avoid asking. A wrong silent link is worse than a
  queued question.
- Filing a stakeholder under `people/` without `people/stakeholders/` or
  `type: stakeholder` (it resolves to the base `person` type and drops out of
  expert routing).
