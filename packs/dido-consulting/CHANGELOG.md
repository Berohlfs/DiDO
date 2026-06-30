# Changelog

All notable changes documented in Keep-a-Changelog shape.

## [0.3.0] - 2026-06-29

- Add four read-only growth-and-reuse skills: `opportunity-finder` (renewals,
  expansions, and inferred new-opportunity signals across the brain),
  `proposal-writer` (proposal draft grounded in cited past work, never filed),
  `deliverable-reuse` (ranked search for reusable deliverables/assets), and
  `expertise-mapper` (thin wrapper over the built-in `find_experts` op, CLI
  `gbrain whoknows`, shaping the query + output with backlink-traced WHY).
- `expertise-mapper` does not reimplement scoring; `find_experts` is a
  first-class gbrain op and the source of truth for the ranking (ADR-001 scopes
  `expert_routing`; ADR-004 the skillpack read-path). The seed is thin on
  `deliverable`/`expertise` pages, so these skills run the right query and
  gap-flag empty/thin results rather than fabricating a result.

## [0.2.0] - 2026-06-29

- Add three on-demand capture skills: `meeting-prep` (read-only prep brief for an
  upcoming client meeting), `risk-review` (recorded risks plus infer-first
  candidate-risk proposals), and `decision-log` (dual-mode: capture writes a
  `decision` page then materializes its edges with `gbrain link`, deduping by
  engagement + title/date against enrich; query returns the decision trail).
- The mutating `decision-log` capture path materializes `owned_by` /
  `requested_by` / `approved_by` edges explicitly after `put`, because
  custom-pack `frontmatter_links` do not auto-materialize in gbrain 0.42.53.0
  (ADR-002, ADR-004). Dedupe-vs-enrich boundary follows ADR-002.

## [0.1.0] - 2026-06-29

- Initial release. Three read-only account-and-status skills: `client-brief`,
  `weekly-account-health`, `executive-summary`. Reads the `dido-engagement`
  ontology through materialized backlinks (custom-pack `frontmatter_links` do
  not auto-materialize in gbrain 0.42.53.0; see ADR-004).
