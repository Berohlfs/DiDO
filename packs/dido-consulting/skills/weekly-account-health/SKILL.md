---
name: dido-weekly-account-health
description: |
  Scheduled (on-demand for now) account-health digest across all active clients.
  Reads each active client's lifecycle status, open risks, engagement movement,
  and opportunities; diffs against the most recent prior run; and SAVES a cited
  report to reports/weekly-account-health/<date>.md. It writes only that report
  file and mutates no brain page. Missing data is gap-flagged, never invented.
triggers:
  - "account health"
  - "weekly account health"
  - "how are our accounts"
  - "account health digest"
  - "account health report"
tools:
  - list
  - get_page
  - get_backlinks
  - graph
  - put_page
mutating: true
writes_pages: false
writes_to:
  - reports/weekly-account-health/
---

# DiDO Weekly Account Health

A weekly digest across active accounts, saved as a dated report. The only write
is the report file under `reports/weekly-account-health/`; no brain page is
created or changed. Cite source slugs; gap-flag empty sections.

## Read path

Traverse materialized edges (`gbrain backlinks` / `gbrain graph`), not raw
frontmatter (ADR-004).

1. **Active clients.** `gbrain list --type client`, then `gbrain get
   clients/<slug>` for each and read `status:` (or `status_override:`). Keep
   the Active ones; count the rest by status for the summary.
2. **Per active client** (compressed Client-Brief traversal):
   - Lifecycle `status:`.
   - Engagements via `gbrain backlinks clients/<slug>` (`client_of`); each
     engagement's `status:` (open | closed) and its latest meeting date
     (`backlinks engagements/<slug>`, `context_for`, newest `date:`) = movement.
   - Open risks via the engagement's `owned_by` risks plus `blocked_by` from
     `graph`; read `severity:` if present, else gap-flag severity.
   - Opportunities via `backlinks clients/<slug>` (`expansion_for` /
     `renewal_for`); each opportunity's `status:` (open | won | lost).
3. **Diff since last run.** List `reports/weekly-account-health/`; the lexically
   greatest filename strictly before today's date is the prior report. Diff per
   client: status changes, new or cleared risks, engagement movement, new
   opportunities. If there is no prior report, this is the first-run baseline
   (state the baseline; no diff).

## Output — write to reports/weekly-account-health/<date>.md

```
# Weekly account health — <date>

## Summary
- Active accounts: <n> · Needing attention: <n>
- Changed since <prior-date | first run>: <one line per change, cited>
- Accounts needing attention: <client list with the reason>  [clients/<slug>]

## <Client Title>  [clients/<slug>]
- Lifecycle: <status>
- Open risks: <Title> (severity: <value | not recorded>)  [risks/<slug>]
- Engagement movement: <Title> status <open|closed>, latest <date>  [engagements/<slug>, meetings/<date>-<slug>]
- Opportunities: <Title> status <open|won|lost>  [opportunities/<slug>]
- Since last week: <delta | first run, baseline | no change>
```

Write the file with `gbrain put reports/weekly-account-health/<date>.md` (or the
equivalent file write). Save the report; do not echo it as the whole answer —
return the path plus the top summary.

## Anti-patterns

- Mutating any client / engagement / risk page. The only write is the report.
- Inventing severity, movement, or a delta. Gap-flag instead.
- Diffing against a future-dated or same-day report. Use the latest report
  strictly before today.
- Listing non-Active clients in the per-client body (count them in the summary).
