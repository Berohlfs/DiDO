# Changelog

All notable changes documented in Keep-a-Changelog shape.

## [0.1.0] - 2026-06-29

- Initial release. Three read-only account-and-status skills: `client-brief`,
  `weekly-account-health`, `executive-summary`. Reads the `dido-engagement`
  ontology through materialized backlinks (custom-pack `frontmatter_links` do
  not auto-materialize in gbrain 0.42.53.0; see ADR-004).
