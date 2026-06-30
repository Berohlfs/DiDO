# BLU-510: Capture, filing, and provenance (the enrich step)

## Goal

Raw artifacts (Fellow meeting transcripts, Cowork sessions) must land as the
right typed page with provenance, filed and linked automatically. The enrich
step infers a page's type and its client/engagement from content, stamps the
frontmatter the `dido-engagement` pack reads, and materializes the typed edges.
It is non-obvious because (a) the linkage must be inferred, not labeled by hand,
(b) low confidence must defer the uncertain link without ever blocking the filing,
and (c) this gbrain build does not auto-materialize custom-pack `frontmatter_links`,
so the edge has to be created explicitly while keeping the frontmatter as the
declarative source of truth.

## Acceptance criteria

- [ ] Each seed artifact becomes a correctly-typed page (`meeting` / `engagement`
      / `client` / `decision` / `risk` / `opportunity`) via slug prefix or explicit
      `type:` frontmatter.
- [ ] The enrich step infers the client and engagement from artifact content and
      stamps `client:` / `engagement:` (including `engagement:` on meetings). It
      creates the engagement and client pages if absent.
- [ ] Every inferred link carries a one-line rationale note on the page so a wrong
      inference is visible in `git diff`.
- [ ] A new `engagement` is stamped `status: open`; a new `opportunity` is stamped
      `status: open` (BLU-509's only inputs).
- [ ] `owner:` is stamped `people/<slug>` from artifact/export context.
- [ ] `gbrain graph engagements/<slug> --depth 1` shows `engagement --client_of--> client`.
- [ ] `gbrain backlinks clients/<slug>` lists the engagement.
- [ ] An artifact whose engagement cannot be inferred still lands as a page; the
      uncertain engagement link is queued as a human question and the page records
      a deferral note.

## Behavior / edge cases

**Type precedence.** `type:` frontmatter beats slug-prefix inference
(`markdown.ts:135`). The enrich step stamps `type:` explicitly so a page never
mis-resolves; the slug prefix is the redundant second signal. Stakeholders are
filed under `people/stakeholders/` or stamped `type: stakeholder`, since the base
`person` prefix is a superset.

**Edge materialization (the load-bearing finding).** In gbrain 0.42.53.0 the
frontmatter-link extractor (`extractPageLinks` → `extractFrontmatterLinks`, run by
the `put_page` auto-link hook and by `gbrain extract`) walks the hardcoded
`FRONTMATTER_LINK_MAP` in `link-extraction.ts`, which mirrors `gbrain-base.yaml`
and carries only base verbs (`works_at`, `attended`, `invested_in`, …). The
pack-aware resolver `frontmatterLinkTypeFromPack` exists but is never called. So
the dido verbs (`client_of`, `owned_by`, `context_for`, `requested_by`,
`approved_by`, `depends_on`, `blocked_by`, `expert_in`, `renewal_for`,
`expansion_for`) do not auto-materialize from frontmatter. The enrich step
therefore does two things per edge:
1. stamps the declaring frontmatter field (the declarative contract: audit trail,
   BLU-509's input, and forward-compatible if gbrain wires the pack resolver), and
2. materializes the edge with `gbrain link <declaring> <referenced> --link-type <verb>`.

The verb and direction are exactly what the frontmatter declares
(declaring-page → referenced-page). `attended` is the exception: it is in the base
map, so meeting `attendees:` and body `[Name](people/slug)` references auto-link.

**Confidence → ask (qualitative, no numeric gate).** When the engagement/client of
an artifact cannot be inferred with confidence, the page is still written (type
stamped, body filed), the uncertain link is left unstamped, a deferral rationale is
written on the page, and a question is appended to `reports/enrich-open-questions.md`.
Filing is never blocked; only the link defers.

**Dedupe vs BLU-512.** Enrich is the automatic path for decision/risk/deliverable
pages; 512's skills are the on-demand path. Dedupe key is `engagement + title/date`.
On overlap enrich creates/updates and the 512 skill annotates the existing page.

**Provenance.** `source_kind` / `source_uri` / `ingested_via` / `ingested_at` are
server-stamped on ingest and survive `put_page` write-through. The enrich step adds
the human-readable rationale notes on top; it does not hand-set provenance columns.

## Test plan (per posture: authoring — gbrain validation gates)

1. Enrich the ABStudios seed thread → typed pages with `engagement:` / `client:`
   frontmatter and a rationale note per inferred link.
2. `gbrain graph engagements/abstudios-sierra --depth 1` → `client_of` edge present
   (direction proven).
3. `gbrain backlinks clients/abstudios` → lists the engagement (reverse reads).
4. Inspect the engagement page → `status: open` in frontmatter.
5. File a Cowork session with no inferable engagement → page lands, question queued
   in `reports/enrich-open-questions.md`, deferral note on the page.

## Reuse & decisions

- Reuses: `dido-engagement` pack (BLU-508), `gbrain put` / `gbrain link` /
  `gbrain graph` / `gbrain backlinks`, the base `attended` auto-link, gbrain's
  `_brain-filing-rules.md` and `ask-user` choice-gate pattern.
- Net-new: explicit-`gbrain link` materialization of dido verbs — the pack's
  `frontmatter_links` resolver is dormant in this build, so frontmatter alone does
  not create the edge; the frontmatter stays as the declarative contract and the
  edge is created explicitly with the same verb/direction.
- ADRs: ADR-002 (infer-first + ask-when-stuck, no numeric gate, rationale-note
  auditability, `status: open` as 509's contract, enrich-vs-512 dedupe).
