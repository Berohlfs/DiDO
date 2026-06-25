# DiDO: Hackathon Brief

> **DiDO** = the company's queryable, time-aware org brain. It captures the knowledge created by everyday work and makes it answerable in plain language.
>
> This is a living doc. The **Problem** and **Planned Solution** are locked. The **What We Built** section is intentionally empty. Fill it in during or after the hack.

---

## 1. Problem

No one on the team can reliably see what's happening across the company.

The work and the decisions don't live in tidy status reports. They live in scattered artifacts inside individuals' tools: Claude Cowork sessions, Fellow meeting recordings, Slack threads, code in Cursor. The knowledge exists and persists, but it's locked inside each person's systems, where others can't find it or even know it's there.

The result:

- **The team flies blind.** Visibility into what's happening is reserved for the few people with the right meetings and relationships. Everyone should be able to see and understand the company well enough to *function like a leader*. Today that visibility is unevenly distributed.
- **Knowledge is siloed and undiscoverable.** The knowledge isn't lost. It's sitting in someone's Fellow, Cowork, or Slack. People forget it exists, don't know where it lives, or can't reach into systems owned by others. Information trapped in another person's tools is effectively invisible.
- **Work is inefficient.** Without shared visibility, people redo analysis, hunt around for context, wait on the one person who knows, and make decisions with partial information.

**Problem statement:** *The whole team, not just leadership, should be able to see and understand what's happening across the company so anyone can function like a leader. That visibility is locked up. The knowledge exists, scattered across people's individual tools (Fellow, Cowork, Slack), where others can't find it or even know it's there. The result is a team that operates on partial information and works inefficiently.*

### Who we're solving for

- **Primary user:** Everyone on the team. The goal is to democratize leader-level visibility. Give any person the ability to see, understand, and act on what's happening across the company, not just the people who happen to be in the right rooms.
- **Why it's universal:** visibility is equally valuable to everyone. A new IC, a senior eng, and a lead all benefit from being able to understand the whole.

### Why now

Work is increasingly done *with* and *through* agents (Cowork, Claude Code, Cursor) and captured tools (Fellow). For the first time the raw material of "what everyone is doing" is digital and capturable by default. It's just not yet captured, connected, or queryable.

---

## 2. Planned Solution

DiDO ingests work artifacts that today live siloed in individuals' tools into a **time-aware org brain** (gbrain) that connects them and answers natural-language questions about them. When the brain hits a gap only a person can fill, it asks that person on **Slack** and folds the answer back in.

Two value props, working together:

1. **Connected knowledge:** unify the knowledge scattered across everyone's individual tools (Fellow, Cowork, Slack) into one place anyone can reach, so information trapped in someone else's systems becomes discoverable and connected.
2. **Democratized transparency:** let *anyone* on the team ask questions and get answers grounded in real artifacts, so everyone can function like a leader.

### Pipeline (maps to the architecture diagram)


| Stage                    | What it does                                                                                       | Hackathon status                                                        |
| ------------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Inputs**               | Claude Cowork, Claude Code, Cursor, Fellow → work artifacts                                        | Cowork + Fellow only, pre-downloaded                                    |
| **Trigger APIs**         | Human-driven or automatic triggers (manual webhook, cron) kick off ingest                          | Manual trigger                                                          |
| **Ingest**               | Normalize raw artifacts into the storage layer (gbrain fork)                                       | Real-ish; manual trigger OK                                             |
| **Storage Intelligence** | gbrain storage + "dreaming with time awareness" that consolidates/reflects over memory across time | **REAL, core asset**                                                    |
| **Outputs**              | Intelligent Brain (GBrain) serves synthesized answers                                              | Real                                                                    |
| **User Usage**           | OPA chat as the front door for human queries; AI query brain later                                 | OPA is the *eventual* front door; hackathon queries hit gbrain directly |
| **Human-in-the-loop**    | When the brain needs info only a human has, it asks via Slack                                      | **REAL**                                                                |


### The query path (important)

The wow moment is a live cross-source query. OPA is *not* a must-build for the hackathon. Resolution: **hackathon queries hit gbrain directly (thin script/CLI); OPA becomes the front door later.** Keeps the demo grounded and the moment intact.

---

## 2.5 The Engine: gbrain (and what "dreaming" means)

DiDO's intelligence layer is **gbrain**. We don't build it from scratch. Most of what we sketched as "the dream pass" is what gbrain does out of the box. Our job is to feed it the right data and point queries at it, not to reinvent agent memory. Inference/execution (running gbrain's LLM-driven skills) is provided by the **MCP client**, so no dedicated agent runtime is required.

> **Why not hermes?** gbrain is designed to be operated by an agent runtime (hermes or openclaw), but those are **single-operator** by design, which is the wrong fit for a **multi-player** team brain. Any MCP client (OPA, Claude Code, the Claude agent we already use) drives gbrain over its MCP server and supplies the inference. So hermes is **out of scope**. We keep gbrain as the brain and let MCP clients be the hands.

### What gbrain is

[gbrain](https://github.com/garrytan/gbrain) is an open-source agent memory system (Garry Tan / YC, MIT-licensed, ~14k stars) that turns plain-text Markdown notes into a **self-wiring knowledge graph an agent can read, write, and reason against.** It runs in Tan's own production setup at tens of thousands of pages. The pieces that matter for DiDO:

- **Markdown brain in git is the source of truth.** Pages organized by subject (`people/`, `companies/`, `meetings/`, `concepts/`, `originals/`). Because it's plain text in version control, you can `git diff` what the brain learned overnight and review every write. That matters a lot for a *transparency* product.
- **"Compiled truth + timeline" page pattern.** Every page has a *compiled truth* section at the top (current best understanding, read first) and an append-only, **dated timeline** below (when each fact was learned/updated). This is the time-awareness mechanism, and history is never destroyed.
- **Self-wiring graph.** Every write extracts entities and creates typed links (`attended`, `works_at`, `invested_in`…) with *zero LLM calls*. Fast, cheap, runs aggressively on big ingests.
- **Hybrid retrieval + citations.** Postgres/pgvector vector search + keyword search, RRF fusion, query expansion, backlink boost; a synthesis layer returns **cited answers** (there's even a `citation-fixer` skill). Grounding is built in.
- **"Thin harness, fat skills."** Behavior lives in ~34 Markdown skill files (`ingest`, `meeting-ingestion`, `enrich`, `query`, `reports`, `cron-scheduler`…). We customize DiDO by *writing skills*, not rewriting a runtime.
- **MCP server.** `gbrain serve` exposes it over MCP, so **OPA can query the brain directly** as the front door.

### Who runs gbrain's skills (inference)

gbrain's deterministic ops (import, link, embed, sync, search) run via its CLI with no agent. Its *judgment* skills (enrich, synthesize, consolidate, query) are LLM-driven and need **an MCP client to supply inference**: OPA, Claude Code, or the Claude agent we're already using, connected to `gbrain serve`. That's the only "runtime" we need. No hermes/openclaw daemon.

### "Dreaming" demystified: a gbrain feature, not our invention

What the diagram calls "Dreaming w/ Time Awareness" is gbrain's **dream cycle**: a background pass (normally a nightly cron, runnable **on-demand**) that ingests, enriches, and **consolidates** memory "while you sleep," explicitly inspired by biological sleep. It's what keeps the brain sharp.

So our earlier "extract → link → reflect" pass = gbrain's ingest + auto-linking + enrich/consolidate, already shipped. For the hackathon the **Dream Trigger (manual)** just kicks this cycle on-demand (an MCP client drives the LLM-skill steps) over our ingested batch.

### "Time awareness": what we get (and the limit)

- ✅ **We get for free:** dated timelines on every page, append-only history (nothing overwritten), and recency-aware retrieval. "What's the latest on X" and "when did we learn Y" work.
- ⚠️ **Caveat:** gbrain's *first-class* temporal querying is limited. "What was true last week but isn't now" and automatic **contradiction reconciliation** are *not* out-of-the-box (per gbrain's own docs, that's "a different product class"). The compiled-truth + timeline pattern *preserves* the history that makes "why did we change our mind?" answerable, but turning that into a clean answer is a **skill we'd author**, not a default. Scope it down rather than overpromise in the demo.

### What this means for the two object types we care about

We said the highest-value things to capture are **Decisions (+ rationale)** and **Blockers / open questions**. In gbrain terms these aren't a custom database. They're **page types / a custom ingest+enrich skill** that writes them into the brain with their timeline and `sources` citations. So "schema" becomes "a thin DiDO skill on top of gbrain's ingest," which is far less to build.

### Why gbrain is the right choice

- **We don't build memory infra.** Consolidation, retrieval, citations, the dream cycle, the graph all exist and run in production.
- **Transparency is native.** Markdown-in-git means every fact is human-readable, diffable, and auditable. The product *is* transparency, and the brain itself is transparent.
- **Citations out of the box.** That's what lets a teammate trust an answer about work they weren't part of.
- **MCP = OPA (and any client) plugs straight in.** No custom query API, and inference comes from the client, so there's no runtime to operate.
- **Customize by writing Markdown skills**, not forking a runtime. Fast iteration during a hackathon.
- **Cheap autonomy** (deterministic linking, job queue). The compounding work is near-free in tokens.

### The one real architectural decision: gbrain is single-operator; DiDO is a team brain

This is why the diagram says **"gbrain fork."** gbrain is designed as a *single-operator* personal brain. DiDO wants a *shared, team* brain everyone can query. The fork is mainly about taking gbrain from one-person memory to a shared org brain (and wiring the Slack human-in-the-loop). For the hackathon's vertical slice (Ryan's data only) this is mostly deferred, but it's the headline thing to build to make DiDO real.

### What DiDO builds on top

- **Ingest adapters** for Cowork + Fellow → gbrain pages (lean on `ingest` / `meeting-ingestion` skills).
- **A thin "decisions + blockers" skill** so those surface cleanly with citations.
- **OPA as the query front door** via gbrain's MCP server.
- **The Slack human-in-the-loop** (gap detected during enrich → Slack → answer written back to the brain → next dream cycle incorporates it).
- **The gbrain fork** toward a shared/team brain (the long-pole; scoped down for the hack).

### How it powers the three demo queries

- **Status** ← recent timeline entries + open blockers across pages.
- **Decision / why** ← decision pages + their dated timeline + linked rationale, with citations.
- **Knowledge lookup** ← gbrain hybrid search + the self-wired graph, returning a synthesized, cited answer.

---

## 3. Hackathon Scope

### Approach: vertical slice on real data

Run the **full pipeline on Ryan's real Cowork + Fellow data only.** Scope demo queries to what that data can truthfully answer. Pitch the org-wide (×N people) vision verbally. This reads as a "foundation to keep building," which is more credible than seeding fake data.

> **Limitation:** one person's data can't answer "what's the *whole company* doing." We demo the mechanism on one person and show it generalizes.

### What must be REAL (not stubbed)

- ✅ **gbrain storage + retrieval:** the core asset we extend after the hack
- ✅ **Human-in-the-loop via Slack:** brain asks a human, gets an answer, incorporates it

### What can be stubbed / manual

- Ingest triggered manually (no cron automation yet)
- OPA front-end (query gbrain directly)
- Inputs beyond Cowork + Fellow (Cursor, Claude Code)

### Success criteria

**Foundation to keep building.** Prioritize real architecture we can extend over demo polish. We win if gbrain + the Slack loop work and the three demo queries return grounded answers from real data.

---

## 4. The Demo

Three queries any teammate might ask, designed backward from the data we have:

1. **Status / what's happening:** *"What's been happening with X this week, and what's blocked?"* → synthesizes across Cowork sessions + Fellow meetings into a status picture, even for work you weren't part of.
2. **Decision / why:** *"Why did we decide to do X, and what was the reasoning?"* → pulls the decision trail across a meeting and a work session.
3. **Knowledge lookup:** *"What do we know about <project / topic>?"* → surfaces knowledge sitting in someone else's tools that you'd otherwise never find.

**Bonus moment:** trigger the human-in-the-loop. The brain hits a gap, pings Ryan on Slack, gets the answer, and completes the query.

> *Refine exact wording once we see what's in the data.*

---

## 5. Open Questions / Risks

- **Data richness:** Is there enough in the Cowork + Fellow exports to make the three queries land? (Verify before locking demo wording.)
- **"Dreaming / time awareness":** Provided by gbrain's dream cycle + compiled-truth/timeline pattern (see §2.5). We trigger it, we don't build it. Remaining risk = (a) does running the dream cycle on our real data produce a good cross-artifact answer, and (b) how much of the "why did we change our mind" temporal story needs a custom skill vs. comes free. Test early.
- **gbrain is single-operator:** The "team brain" requires forking gbrain toward shared/multi-user memory. Scoped down for the hack (one person's data), but it's the long-pole to make DiDO production-grade.
- **Grounding / citations:** ✅ Native to gbrain. Answers come back cited to the source page/artifact (see §2.5).
- **Slack loop latency:** Is the human-in-the-loop fast enough to show live, or do we pre-stage it?
- **Privacy/scope:** If everyone can see everything, where are the boundaries? Democratized visibility is the point, but some things (HR, comp, sensitive deals) need limits. (Out of scope for hack, but someone will ask.)

---

## 6. What We Built

> *Fill in during / after the hackathon.*

### Shipped

- 

### Deviations from plan

- 

### Demo notes (what worked live, what was staged)

- 

### Next steps to make it real

- 

