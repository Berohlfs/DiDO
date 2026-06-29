# ADR-002: enrich filing by inference, ask when stuck

Status: Accepted
Date: 2026-06-29
Ticket: BLU-510

## Context

Raw artifacts (Fellow meeting transcripts, Cowork sessions) must land in the brain
as the right typed page with provenance, filed and linked under the
`dido-engagement` ontology (ADR-001), with no manual labeling. The enrich step
infers a page's type and its client/engagement from content and stamps the
frontmatter the pack reads. Two forces shape the design: inference is sometimes
wrong, and the linkage is sometimes genuinely uninferable. Neither may produce a
dropped artifact, and a wrong inference must be cheap to catch.

The verification posture is authoring: gbrain validation gates, not unit tests.

## Decision

### Infer first, ask only when stuck

The enrich step infers type and client/engagement from artifact content and stamps
the fields directly (`client:` on engagements, `engagement:` on meetings /
decisions / risks / deliverables, `owner:`, `requested_by:`, etc.). An explicit
`engagement:` hint in the artifact is honored when present, never required. When a
link cannot be inferred with confidence, the step routes a question to a human (the
`reports/enrich-open-questions.md` list, or gbrain's `ask-user` choice gate when a
human is live) and writes the answer back.

### No numeric confidence gate

Confidence is a qualitative call, not a threshold. A numeric cutoff would be false
precision: the same 0.7 score means "obvious" for one field and "coin-flip" for
another, and tuning the number becomes the work instead of filing the artifact. The
step asks when a reasonable reader would be unsure, and the rationale note (below)
makes a wrong call visible regardless of any score.

### Filing is never blocked; the link defers

Low confidence blocks only the uncertain link, never the artifact. The page is
always written with its type and body. The uncertain field is left unstamped, a
`DEFERRED` line is added to the page's `## Provenance` section, and a row is queued
in the open-questions list. This guarantees no artifact is lost to uncertainty.

### A rationale note per inferred link (git-diff auditability)

Every inferred link gets a one-line rationale on the page, dated `[enrich <date>]`,
in a `## Provenance` section. Pages write through to the source git repo, so a
wrong inference shows up in `git diff` and is a one-line fix. This is the safety
net that lets the step infer aggressively without a numeric gate: the cost of a
wrong inference is a visible, cheap correction, not a silent corruption.

### `status: open` is BLU-509's contract

When enrich creates an engagement it stamps `status: open`; a new opportunity gets
`status: open`. These two frontmatter fields are BLU-509's only inputs. The enrich
step owns writing them at creation; BLU-509 derives `client.status` from them.

### Enrich vs BLU-512 dedupe boundary

Enrich is the automatic page-creating path for decision/risk/deliverable pages.
BLU-512's skills are the on-demand path. The dedupe key is `engagement +
title/date`: on overlap enrich creates or updates the page and the 512 skill
annotates the existing one. There is never a second page for the same decision.

## Alternatives considered

### Auto-materialize edges from pack frontmatter_links (does not work in this build)

The obvious design (ADR-001's stated model) is that stamping `client:` on an
engagement materializes the `client_of` edge automatically from the pack's
`frontmatter_links`. It does not in gbrain 0.42.53.0. The frontmatter-link
extractor (`extractPageLinks` → `extractFrontmatterLinks`, run by the `put_page`
auto-link hook and `gbrain extract`) walks the hardcoded `FRONTMATTER_LINK_MAP` in
`link-extraction.ts`, which mirrors `gbrain-base.yaml` and carries only base verbs
(`works_at`, `attended`, `invested_in`, …). The pack-aware resolver
`frontmatterLinkTypeFromPack` exists but is never called. So the dido verbs
(`client_of`, `owned_by`, `context_for`, `requested_by`, `approved_by`,
`depends_on`, `blocked_by`, `expert_in`, `renewal_for`, `expansion_for`) never
auto-fire from frontmatter. Verified on the validation brain: a put with
`client: clients/abstudios` produced zero links until materialized explicitly.

We do not patch `gbrain/src` (out of scope and against the milestone rule). So the
enrich step stamps the frontmatter AND materializes each edge with
`gbrain link <declaring> <referenced> --link-type <verb>`, in the direction the
frontmatter declares. The frontmatter stays as the declarative source of truth:
it is the audit record, it is BLU-509's input, and it is forward-compatible if a
later gbrain build wires the pack resolver, at which point the explicit calls
become redundant rather than wrong. `attended` is the exception: it is a base verb,
so meeting `attendees:` and body `[Name](people/<slug>)` references auto-link with
no explicit call (confirmed on the seed).

### A second "owns" verb for the reverse reading (rejected, per ADR-001)

The reverse view (an engagement's deliverables/meetings) is a backlinks query over
the existing edges, not a declared inverse verb. Proven on the seed:
`gbrain backlinks engagements/abstudios-sierra` returns the five meetings, two
decisions, and one risk.

## Consequences

- BLU-509 can read `status: open` from `engagements/abstudios-sierra` and
  `opportunities/florida-district` immediately.
- Edge direction is proven on real enriched pages:
  `engagements/abstudios-sierra --client_of--> clients/abstudios`.
- The enrich step has a build-specific dependency on explicit `gbrain link`. If a
  future gbrain wires pack `frontmatter_links`, drop the explicit calls; the
  frontmatter already carries the same edges. The dependency is documented in the
  skill and `filing-rules.md` so it is not mistaken for incidental.
- A wrong inference is a one-line `git diff` fix, not a silent graph error.
