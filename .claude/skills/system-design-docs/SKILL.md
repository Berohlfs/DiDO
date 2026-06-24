---
name: system-design-docs
description: >-
  Create system design / architecture documentation as Markdown files with inline
  Mermaid diagrams, written to docs/system-design/. Use this whenever the user wants
  to document, diagram, map out, or visualize a system's architecture, data flow,
  components, services, or request lifecycle — including phrases like "document the
  architecture", "create a system design doc", "diagram this system", "draw the
  architecture", "map out how X works", or when they hand over an architecture
  screenshot to be turned into docs. Also trigger when the user wants codebase or
  architecture context written down for future Claude Code agents to read. The output
  is deliberately dual-purpose: human-readable AND high-signal context for agents, so
  every diagram is always paired with prose that names each component, its
  responsibility, where it lives in the codebase, and the data/contract flowing
  between components.
---

# System Design Docs

Produce Markdown files under `docs/system-design/` that combine **Mermaid diagrams**
(which render inline on GitHub and in most IDEs) with **structured prose**.

The prose matters as much as the picture. These docs are read by humans *and* loaded
as context by future agents. A diagram alone is low-signal: a box labeled "Worker"
tells an agent nothing about what it does or where to find it. Every diagram must be
surrounded by text that names components, their responsibilities, their real code
locations, and the contracts between them. Mermaid is plain text, so an agent reads the
diagram *source* directly — lean into that by keeping labels meaningful.

## Workflow

### 1. Gather inputs

- **Read the prompt** describing the architecture. Pull out components, boundaries,
  flows, and any tech named.
- **Check for a screenshot / image.**
  - If one is provided: study it closely. Extract every box, arrow, label, grouping,
    and annotation. Where a box is ambiguous, ask rather than guess.
  - If none is provided: **before writing, ask the user whether they can share
    something that would make the doc accurate** — an architecture screenshot, a
    whiteboard photo, an existing diagram, or infra-as-code (docker-compose, k8s
    manifests, Terraform). Frame it as a quality boost, not a blocker. If they have
    nothing, proceed from the prompt plus the codebase.
- **Explore the repo if you're inside it.** Entry points, service boundaries, package
  layout, config, and infra files let you ground the doc in reality. Real file paths
  are the single highest-value thing you can hand a future agent — prefer them over
  generic descriptions.

### 2. Decide what to draw

Match the diagram type to what you're describing. Don't cram everything into one giant
graph — several small, focused diagrams beat one unreadable one.

| You're describing… | Use | Mermaid type |
| --- | --- | --- |
| Boxes-and-arrows system layout, services, dependencies | Architecture / context | `flowchart` (aka `graph`) |
| A request or process unfolding over time across components | Sequence of interactions | `sequenceDiagram` |
| Data model, tables, entities and relationships | Data model | `erDiagram` |
| Lifecycle of an entity (order: draft → paid → shipped) | State machine | `stateDiagram-v2` |
| Domain objects / class structure | Class model | `classDiagram` |
| High-level system-of-systems context | C4 context | `C4Context` (experimental) |

A typical `overview.md` has a context flowchart + a components table + 1–2 key sequence
diagrams. Add an `erDiagram` when data shape matters.

### 3. Write the doc — use the template in the next section.

### 4. Validate the Mermaid

Syntax errors render as a red error box, which is worse than no diagram.

- If `npx` is available, render each diagram to catch errors before saving:
  `npx -y @mermaid-js/mermaid-cli -i /tmp/d.mmd -o /tmp/d.svg`
  (no network? skip and review manually).
- Otherwise review against the **Mermaid checklist** below.

### 5. Save

- Write to `docs/system-design/<kebab-name>.md`; create the directory if missing.
- **Naming convention:**
  - `overview.md` — the whole system at a glance (start here for any new system).
  - One file per major service / bounded context otherwise:
    `payment-service.md`, `ingestion-pipeline.md`, `auth-flow.md`.
- If more than one doc exists, keep `overview.md` linking out to the others so both
  humans and agents have a single entry point.

## Document template

Follow this structure. Keep the headings; drop sections that genuinely don't apply
(marked *optional*). Fill the `> agent-context` block — it's what makes the doc useful
to agents that can only see this file.

```markdown
# <System / Service Name>

> **Status:** draft | current | deprecated
> **Last updated:** YYYY-MM-DD
> **Primary code:** `path/to/service/`, `path/to/related/`
> **Related docs:** [overview](./overview.md), [auth-flow](./auth-flow.md)

## Summary

One short paragraph: what this system does, who/what calls it, and the single most
important thing to understand about it. Optimize for an agent reading only this.

## Context diagram

How this system sits among its neighbors.

​```mermaid
flowchart LR
    user([User]) --> web[Web App]
    web --> api[API Gateway]
    api --> orders[Order Service]
    orders --> db[(Postgres)]
    orders --> bus[[Event Bus]]
    bus --> notify[Notification Worker]
​```

## Components

| Component | Responsibility | Code location | Tech |
| --- | --- | --- | --- |
| API Gateway | Auth, routing, rate limiting | `gateway/` | Kong |
| Order Service | Order lifecycle, validation | `services/orders/` | Go |
| Notification Worker | Consumes events, sends email/SMS | `workers/notify/` | Python |

## Key flows

Name each non-trivial flow and diagram it. This is where agents learn *how* things
actually move through the system.

### Placing an order

​```mermaid
sequenceDiagram
    actor User
    participant Web
    participant API as Order Service
    participant DB as Postgres
    participant Bus as Event Bus
    User->>Web: Submit order
    Web->>API: POST /orders
    API->>DB: INSERT order (status=pending)
    API->>Bus: publish OrderCreated
    API-->>Web: 201 { order_id }
    Web-->>User: Confirmation
​```

## Data model  *(optional — include when data shape matters)*

​```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "appears in"
​```

## Design decisions & trade-offs

The "why". Capture choices a future change might otherwise unknowingly break.
- **Async notifications via event bus** — decouples order writes from email latency;
  trade-off is eventual consistency on notification state.
- **Postgres over a queue for the order of record** — orders need transactional
  guarantees; the bus is fire-and-forget downstream.

## Operational notes  *(optional)*

Scaling characteristics, known failure modes, idempotency, retries, key env vars.

## For agents

Explicit pointers that save future agents a search:
- Adding an order field → migration in `services/orders/db/`, DTO in `services/orders/api/`.
- New event type → register in `services/orders/events/` **and** add a handler in `workers/notify/`.
- Gotchas: `OrderCreated` is published *after* commit; never assume the worker sees
  uncommitted state.

## Glossary  *(optional)*

- **Bounded context** — …
```

(The `​` zero-width characters before each ```` ```mermaid ```` above are only to keep
this template readable inside a fenced block — write normal triple backticks in the real
doc.)

## Mermaid checklist (common breakers)

- **Quote labels** with spaces + special chars or reserved words:
  `n1["Cache (Redis)"]`, not `n1[Cache (Redis)]`.
- **Avoid a node literally named `end`** in flowcharts — lowercase `end` collides with
  the block keyword and breaks parsing. Capitalize (`End`) or rename.
- **Sequence diagrams:** declare `participant` / `actor` up front to control left-to-right
  order; use `as` for short aliases.
- **Line breaks inside a label:** use `<br/>`. Avoid raw `<`, `>`, `&` unless you mean HTML.
- **One statement per line** — Mermaid is newline-sensitive.
- **Subgraphs:** `subgraph id ["Title"]` … `end`. Give them IDs if you'll link to them.
- **Keep it under ~15–20 nodes** per diagram. Beyond that, split into focused diagrams.
- **Arrow types carry meaning:** `-->` solid (sync/strong), `-.->` dotted (async/optional/event).
  Be consistent and note the convention if it isn't obvious.

## Examples of the workflow in action

**Prompt only, no image:**
> User: "Document the architecture of our ingestion pipeline."
> → No screenshot. Ask: "Happy to. Do you have an architecture screenshot, a
> docker-compose/k8s file, or can you point me at the pipeline directory? It'll make the
> diagram match reality. If not, I'll work from your description." → Then explore the repo
> if available, write `docs/system-design/ingestion-pipeline.md` with a context flowchart,
> components table tied to real paths, and a sequence diagram of one message's journey.

**Screenshot provided:**
> User uploads a whiteboard photo of services and arrows.
> → Transcribe every box and arrow into a `flowchart`, confirm any unreadable labels,
> add the components table and flows, save to `docs/system-design/overview.md`.