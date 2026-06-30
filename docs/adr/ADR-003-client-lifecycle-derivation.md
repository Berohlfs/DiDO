# ADR-003: client lifecycle status as a derived label

Status: Accepted
Date: 2026-06-29
Ticket: BLU-509

## Context

Each client needs a lifecycle label (Active, Past, Prospect, Lost) so downstream
skills (Client Brief BLU-511, and 512/513) can read and filter by it. The label is
state, not value: no scoring, no health number. The state is fully determined by
data the brain already holds, the `status:` frontmatter on a client's engagements
(`open` | `closed`) and opportunities (`open` | `won` | `lost`), stamped at filing
time by the enrich step (ADR-002).

Three forces shaped this:

1. gbrain cannot carry `status` as a pack-declared fact. The facts-fence kind is a
   hardcoded enum and typed-claim columns are numeric/text-scalar only (ADR-001,
   brief headline 1). So the label lives in page frontmatter.
2. The derivation must run somewhere. The obvious home is a dream-cycle phase, but
   gbrain's `CyclePhase` is a closed hardcoded 22-member union (`cycle.ts`); a
   pack's `phases:` can only opt into existing phase names, it cannot add one.
3. A human sometimes needs to pin a status against the derived value.

Verification posture is authoring: gbrain validation gates, not unit tests.

## Decision

### Precedence model (first match wins)

1. **Active** — at least one engagement `status: open`.
2. **Past** — has engagement(s), all `status: closed`, none open.
3. **Prospect** — no engagement ever; at least one opportunity `status: open`.
4. **Lost** — no engagement ever; opportunities exist and all are `status: lost`.
5. Default (no engagements, no opportunities): leave `status` unset.

Engagement history outranks opportunity-only states. A client with a closed
engagement and a separately-lost opportunity is **Past**, not Lost: once a client
has ever been engaged, its lifecycle is Active or Past, and an unsold opportunity
does not regress it to a pre-engagement state. Encoding this as plain precedence
(rule 2 is reached before rules 3-4) keeps the logic a fixed ladder with no
special cases.

### status vs status_override

`status:` on the client page is the derived field, owned by this skill.
`status_override:` is a manual human pin. When `status_override` is present,
derivation is SKIPPED for that client and the override value stands. The skill
reads `status_override` but never writes it. This keeps the human pin and the
machine derivation in separate fields so a re-run never clobbers a deliberate
override, and removing the override line lets derivation resume on the next run.

### Skill, not a dream phase

The derivation runs as the on-demand skill `dido-client-lifecycle-status`
(`packs/dido-engagement/lifecycle-status/SKILL.md`), which enumerates clients,
reads each one's engagement and opportunity `status:`, applies the precedence
ladder, and writes `status` back with `gbrain put`. It runs manually now; a
nightly schedule is wired by BLU-517 via gbrain cron, not by this ticket.

### Filter-by-frontmatter command

`gbrain list` filters by `--type` and `--tag` only, with no arbitrary-frontmatter
predicate, and `gbrain query` / `search` are semantic and non-deterministic. The
settled, index-free path enumerates clients by type and reads the `status:`
frontmatter off each page:

```
gbrain list --type client --limit 200 | awk '{print $1}' | while read s; do
  st=$(gbrain get "$s" | sed -n 's/^status:[[:space:]]*//p' | head -1)
  echo "$s	${st:-<unset>}"
done
```

Append `| awk -F'\t' '$2=="Active"{print $1}'` to filter to one status.

## Alternatives considered

- **Pack-declared `status` fact.** Rejected: the facts kind enum and claim columns
  cannot represent a categorical status (ADR-001). Frontmatter is the only seat.
- **Dream-cycle phase.** Rejected: adding a phase forks the engine; `CyclePhase`
  is closed (`cycle.ts`). A skill plus a later cron schedule gets the same nightly
  behavior with zero engine changes.
- **A scored health metric.** Out of scope by ticket intent. We track state, not
  value.
- **Enumerate engagements by walking frontmatter.** Used only as a fallback. The
  primary traversal is `gbrain backlinks`, because gbrain 0.42.53.0 does not
  auto-materialize custom-pack `frontmatter_links` (ADR-002); the `client_of` /
  `expansion_for` / `renewal_for` edges are the materialized, reliable source.

## Consequences

- Downstream skills read client lifecycle from the `status:` frontmatter key on
  `client` pages; values are exactly `Active` / `Past` / `Prospect` / `Lost`, or
  unset. They filter with the command above.
- The label is only as fresh as the last skill run until BLU-517 schedules it.
- A wrong derivation is visible in `git diff` on the client page (pages write
  through to the source repo), consistent with the ADR-002 audit model.
