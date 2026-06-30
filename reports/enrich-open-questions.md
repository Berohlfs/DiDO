# Enrich open questions

Links the enrich step (BLU-510) could not infer with confidence. Filing was not
blocked: each artifact landed as a page; only the uncertain link defers. A human
answers here, then the enrich step stamps the field, materializes the edge with
`gbrain link`, and marks the row `RESOLVED`.

| # | Artifact (page) | Uncertain link | Candidate answers | Status |
| -- | -- | -- | -- | -- |
| 1 | `notes/2026-03-17-agentic-engineering-research` | `engagement:` | (a) internal R&D, no engagement; (b) a Sierra internal-tools engagement if one is opened | OPEN |
| 2 | `notes/2026-03-17-agentic-engineering-refinement` | `engagement:` | (a) internal R&D, no engagement; (b) same internal engagement as #1 | OPEN |

## Notes

Both artifacts are internal Sierra Cowork sessions about agentic engineering best
practices. No client or engagement is named in their content, so the enrich step
filed them as `note` pages with a `DEFERRED` provenance line and left
`engagement:` unstamped rather than guess a client link. If these should hang off
an internal engagement, create it (`status: open`), answer the row, and link.
