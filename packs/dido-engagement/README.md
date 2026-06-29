# dido-engagement schema pack

Makes the client engagement the primary object of Sierra's company brain. Adds nine
engagement-domain page types (client, engagement, stakeholder, deliverable, decision,
risk, opportunity, expertise, asset), redeclares `meeting`, and wires eleven typed link
verbs. `extends: gbrain-base` inherits the base types (person, source, note, ...).

Rationale for the type set, the verb wiring, and the status-as-frontmatter choice is in
`docs/adr/ADR-001-dido-engagement-ontology.md`.

## Install

The runtime pack file is `pack.yaml`. Copy this directory's `dido-engagement.yaml` to the
brain's schema-pack dir as `pack.yaml` (the loader resolves `pack.yaml` before `pack.json`):

```bash
mkdir -p "$GBRAIN_HOME/.gbrain/schema-packs/dido-engagement"
cp dido-engagement.yaml "$GBRAIN_HOME/.gbrain/schema-packs/dido-engagement/pack.yaml"
```

## Activate

```bash
gbrain schema validate dido-engagement      # manifest shape
gbrain schema lint dido-engagement --with-db # dangling-ref + DB-plane rules
gbrain schema use dido-engagement            # activate brain-wide
gbrain schema sync --apply                   # backfill page.type for matching prefixes
```

`sync --apply` only types pages whose slug matches a declared prefix (clients/,
engagements/, ...). Date-prefixed seed notes match nothing and stay orphans until an
enrich step files typed pages.

## Isolation

Run every command with `GBRAIN_HOME` pointed at an isolated brain so activation and
`sync --apply` never touch shared state:

```bash
GBRAIN_HOME="$HOME/.gbrain-dido" gbrain schema use dido-engagement
```

Without `GBRAIN_HOME` the commands hit the default brain and mutate it.
