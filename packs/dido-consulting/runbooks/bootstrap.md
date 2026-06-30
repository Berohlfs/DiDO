# Bootstrap

Post-scaffold steps. gbrain displays this but does NOT auto-execute. The agent
reads it and walks per-step at its own discretion.

1. Confirm the `dido-engagement` schema pack is active in this brain
   (`gbrain schema use dido-engagement`). These skills read its page types and
   the materialized edges (`client_of`, `owned_by`, `context_for`,
   `expansion_for`, `renewal_for`).
2. Confirm the seed has at least one client with an open engagement
   (`gbrain list --type client`, then `gbrain backlinks clients/<slug>`).
3. Try a trigger: "client brief" → expect a one-page cited brief that
   gap-flags any missing section rather than inventing it.
4. `weekly-account-health` writes to `reports/weekly-account-health/<date>.md`.
   Ensure that directory is writable in the brain's source repo.
