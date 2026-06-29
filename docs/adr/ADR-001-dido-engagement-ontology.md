# ADR-001: dido-engagement ontology

Status: Accepted
Date: 2026-06-29
Ticket: BLU-508

## Context

DiDO is a gbrain fork for Sierra's company brain. The brain's primary object is the client
engagement. gbrain's default taxonomy (gbrain-base) is built around people, companies, and
deals, which does not model consulting work. We author a gbrain schema pack,
`dido-engagement`, that makes the engagement first-class and wires the relationships a
consulting brain needs (who owns a deliverable, what blocks an engagement, who can approve
a decision, who is an expert in what).

The pack is pure authoring. Verification is the gbrain schema validation gates (validate,
lint --with-db, use, sync --apply, explain), not unit tests. No `gbrain/src` changes.

## Decision

### Ten page types over five primitives

`extends: gbrain-base` so the pack inherits the base types (person, source, note, and the
rest). It adds nine engagement-domain types and redeclares `meeting`:

| Type | primitive | prefix | extractable | expert_routing |
| -- | -- | -- | -- | -- |
| client | entity | clients/ | yes | no |
| engagement | entity | engagements/ | yes | no |
| stakeholder | entity | people/stakeholders/ | yes | yes |
| deliverable | annotation | deliverables/ | yes | no |
| decision | temporal | decisions/ | yes | no |
| risk | temporal | risks/ | yes | no |
| opportunity | temporal | opportunities/ | yes | no |
| expertise | concept | expertise/ | no | yes |
| asset | concept | assets/ | no | no |
| meeting | temporal | meetings/ | yes | no |

`primitive` is the closed enum entity|temporal|concept|annotation|media. Clients,
engagements, and stakeholders are durable entity surfaces. Decisions, risks, and
opportunities are events in time (temporal). A deliverable is an annotation: it annotates
an engagement, it does not stand alone. Expertise and assets are concepts (reusable
knowledge and reusable artifacts).

`stakeholder` is declared before any type carrying the `people/` prefix so a page at
`people/stakeholders/*` resolves to stakeholder, not the inherited person. Path-prefix
inference is first-match-wins.

### Verbs are driven by frontmatter_links with no inverse

Every relationship is materialized from `frontmatter_links` (deterministic, zero-LLM). The
pack's `frontmatter_links` form is `{page_type, fields, link_type}` only. Each edge points
declaring-page to referenced-page. There is no inverse or direction knob, by schema design.

| Verb | from -> to | Created from |
| -- | -- | -- |
| client_of | engagement -> client | engagement `client:` |
| owned_by | deliverable/decision/risk -> engagement | child `engagement:` |
| context_for | meeting -> engagement | meeting `engagement:` |
| requested_by | decision/deliverable -> stakeholder | `requested_by:` |
| approved_by | decision -> stakeholder | `approved_by:` |
| depends_on | deliverable/decision -> deliverable/decision | `depends_on:` |
| blocked_by | engagement/deliverable/decision -> risk | `blocked_by:` |
| expert_in | stakeholder -> expertise | stakeholder `expert_in:` |
| renewal_for | opportunity -> client | opportunity `renewal_for:` |
| expansion_for | opportunity -> client | opportunity `expansion_for:` |
| similar_to | engagement -> engagement | declarative-only |

Verbs are named after the field that creates them. The reverse reading is a backlink
traversal: an engagement's "owns" view of its deliverables is `gbrain backlinks` over the
`owned_by` edges, not a separate `owns` verb. A verb that can be declared from several page
types (owned_by, depends_on, blocked_by, requested_by) gets one `frontmatter_links` entry
per declaring type, because `page_type` is a single string.

`meeting` is redeclared in the pack rather than left to inheritance. `gbrain schema lint`
validates `frontmatter_links.page_type` against the manifest as loaded from disk
(`loadPackFromFile`), not against the extends-merged set. `context_for` declares from
`meeting`, so `meeting` must be a local page_type or lint errors with
`frontmatter_links_undeclared_page_type`. The redeclaration matches the base meeting type
(temporal, meetings/), so runtime behavior is unchanged.

### expert_in originates on stakeholder, not person

The ticket's verb sketch named the expert as `person`. We wire `expert_in` from
`stakeholder` instead. `expert_routing` is scoped to stakeholder and expertise, and
`gbrain whoknows` / `find_experts` filters candidates to `expert_routing` types. An edge
from the inherited, non-routed `person` type would never surface in expert search, so it
would be inert for the feature it exists to serve. Declaring `person` locally just to host
the verb would also force a choice between giving person `expert_routing` (which widens the
routed set beyond stakeholder + expertise) or leaving the verb dead. Originating the edge
on stakeholder keeps the routed set at exactly stakeholder + expertise and keeps the verb
live.

### Status lives in frontmatter, not as a fact

`engagement.status` is open|closed and `opportunity.status` is open|won|lost. These are page
frontmatter, enforced by convention and skills, not declared as a pack fact.

## Alternatives considered

### A pack-declared status enum fact (rejected)

The obvious move is to model status as a typed fact so it is queryable like other claims.
gbrain cannot express this. The facts kind is a hardcoded enum (event|preference|commitment
|belief|fact in `facts-fence.ts`), not pack-driven. The typed-claim columns are numeric and
text-scalar only (`claim_metric`, `claim_value`, `claim_unit`, `claim_period`); there is no
column for an enum membership. A pack's `takes_kinds` widens the takes-table kind, which is
a different axis and still does not give an enum-valued status fact. So status stays in
frontmatter. `client.status` is derived (BLU-509), not stored.

### Inverse verbs for the reverse reading (rejected)

We could declare `owns` as the inverse of `owned_by`, `requested` as the inverse of
`requested_by`, and so on, to make both directions first-class. The pack `frontmatter_links`
schema has no inverse field, and a pack-declared frontmatter link only materializes the
outgoing edge. The reverse direction is already available through backlink traversal, so a
second declared verb would add a name with no new edges and double the surface to keep
consistent. We rely on backlinks for every reverse reading.

### similar_to with an inference rule (rejected for now)

`similar_to` (engagement to engagement) is declared but has no `frontmatter_links` wiring
and no inference rule, so it never auto-fires. A future pattern library writes these edges
explicitly (`gbrain link`). Auto-firing similarity would need an inference rule or an LLM
pass that does not exist yet, and a wrong-but-confident similarity edge is worse than none.

## Consequences

- The brain is queryable by engagement-centric relationships as soon as typed pages exist.
- Edge direction is proven on a real enriched page in BLU-510, not here. With no typed
  pages yet, the seed notes remain orphans and `sync --apply` types zero rows, which is the
  expected pre-enrichment state.
- BLU-510's enrich step must stamp the field names this pack reads: `client:` on
  engagements; `engagement:` on deliverables, decisions, risks, and meetings;
  `requested_by:` / `approved_by:` / `depends_on:` / `blocked_by:` where applicable;
  `expert_in:` on stakeholders; `renewal_for:` / `expansion_for:` on opportunities.
- Stakeholders must be filed under `people/stakeholders/` (or carry explicit
  `type: stakeholder` frontmatter) so they do not resolve to the inherited person type.
