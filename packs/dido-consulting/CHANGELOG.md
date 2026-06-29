# Changelog

All notable changes documented in Keep-a-Changelog shape.

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
