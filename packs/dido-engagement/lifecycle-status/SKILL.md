---
name: dido-client-lifecycle-status
description: |
  Derive each client's lifecycle status (Active / Past / Prospect / Lost) from the
  status of its engagements and opportunities, and write it back to the client page
  frontmatter as `status:`. Tracks state, not value: no scoring. A manual pin
  (`status_override:`) skips derivation for that client. Runs on demand now; a
  nightly schedule waits on BLU-517.
triggers:
  - "derive client lifecycle status"
  - "recompute client statuses"
  - "refresh client lifecycle"
  - "update client status labels"
  - "what is this client's lifecycle status"
tools:
  - list
  - get_page
  - get_backlinks
  - put_page
mutating: true
writes_pages: true
writes_to:
  - clients/
---

# DiDO Client Lifecycle Status

Label every client with a derived lifecycle state from the status of its
engagements and opportunities. The label is a frontmatter field on the client
page, not a fact (status is not a pack-declarable fact kind in gbrain; see
ADR-001 and ADR-003).

## States and precedence (first match wins)

Read `status:` off the client's engagement and opportunity pages, then apply in
this order. Precedence is the contract: engagement history outranks
opportunity-only states.

1. **Active** — at least one engagement `status: open`.
2. **Past** — has engagement(s), all `status: closed`, none open.
3. **Prospect** — no engagement ever; at least one opportunity `status: open`.
4. **Lost** — no engagement ever; opportunities exist and all are `status: lost`.

Default (no engagements and no opportunities): leave `status` unset.

A client with a closed engagement AND a separately-lost opportunity is **Past**:
engagement history at rule 2 is reached before any opportunity-only rule.

## Override

`status_override:` on the client page is a manual pin. When present, derivation is
SKIPPED for that client and the override value stands. `status:` is the derived
field; `status_override:` is the human pin. The skill never writes
`status_override`; it only reads it and steps over the client.

## Procedure

For each client (`gbrain list --type client`):

1. Read the client page. If it carries `status_override:`, skip it and move on.
2. Find its engagements and opportunities through the explicit graph edges, not
   frontmatter alone (see build note below): `gbrain backlinks clients/<slug>`
   returns one row per incoming edge. `link_type: client_of` rows are
   engagements; `link_type: expansion_for` / `renewal_for` rows are opportunities
   (`from_slug` is the related page).
3. Read `status:` off each related engagement and opportunity page.
4. Apply the precedence rule above to get the derived value (or none).
5. Write the value back into the client page frontmatter with `gbrain put`,
   preserving the existing frontmatter and body. If the rule yields none, remove
   any stale `status:`.

This is read-deterministic and LLM-free: every input is a literal `status:`
frontmatter string and the rule is a fixed precedence ladder.

## Build note — why backlinks, not frontmatter walk

gbrain 0.42.53.0 does not auto-materialize custom-pack `frontmatter_links`; the
dido edges were created with explicit `gbrain link` (see ADR-002 and the enrich
filing-rules). So the reliable way to enumerate a client's engagements and
opportunities is the materialized edge set via `gbrain backlinks`. Reading the
engagement's `client:` / the opportunity's `expansion_for:` frontmatter is the
equivalent fallback if an edge is missing.

## Runtime — skill, not a dream phase

This derivation does not run as a cycle phase. gbrain's `CyclePhase` is a closed
hardcoded union (`cycle.ts`); a pack's `phases:` can only opt into existing phase
names, it cannot add one (ADR-003). So this is a skill invoked on demand. A
nightly schedule (gbrain cron / `cron-scheduler`) is wired by BLU-517.

## Filter clients by status

`gbrain list` filters by `--type` and `--tag`, not by arbitrary frontmatter. To
list/group clients by lifecycle status, enumerate clients and read the `status:`
frontmatter off each page (no new index):

```
# all clients with their status
gbrain list --type client --limit 200 | awk '{print $1}' | while read s; do
  st=$(gbrain get "$s" | sed -n 's/^status:[[:space:]]*//p' | head -1)
  echo "$s	${st:-<unset>}"
done

# only Active clients: append  | awk -F'\t' '$2=="Active"{print $1}'
```

## Anti-patterns

- Scoring or ranking clients. This tracks state only.
- Overwriting `status` on a client that carries `status_override`.
- Treating an opportunity-only state as outranking engagement history. A client
  that has ever had an engagement is Active or Past, never Prospect or Lost.
- Enumerating a client's engagements by walking frontmatter and assuming the edge
  exists. In this build, traverse `gbrain backlinks`.
