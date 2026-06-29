# ConsultingBrain for DiDO — Proposal & Effort Estimate

> **Status:** draft for review (round 1) — historical rationale.
> **Date:** 2026-06-29
> **Superseded on specifics:** the ontology in §7/§8 (link verbs, `expert_routing` flags) is the round-1 sketch. For the built ontology — corrected verb directions (`owned_by`, `context_for`, `requested_by`, `approved_by`), the `frontmatter_links` inverse constraint, and `expert_routing` on stakeholder + expertise only — see `docs/mvp-execution-plan.md` §3 and BLU-508. Read this doc for the why, not the exact field list.
> **Scope of this doc:** plan + effort only. No execution until we agree the go-forward.
> **Decisions locked going in (from kickoff):**
> - **Goal:** internal brain for Sierra's own client/engagement work (not a product for outside firms — yet).
> - **Relationship to DiDO:** extend DiDO as a layer if possible; pivot the core model only if extending proves insufficient.
> - **Plan depth:** full vision — cover the whole design doc (ontology, ~13 skills, importance model, pattern library, enrichment, cron).

---

## 1. TL;DR

The consulting design doc's central recommendation — *"don't fork GBrain deeply; build ConsultingBrain as a reusable layer of ontology + skills + enrichment + cron + relationship schema"* — turns out to describe a mechanism **GBrain already ships natively**: a **schema pack** (`.gbrain-schema`: page types, link verbs, fact-extraction targets, expert-routing/importance flags, filing rules) plus a **skillpack** (`.gbrain-skillpack`: the markdown skills), both installable and version-pinned without touching the engine.

So the recommended approach is achievable as **an extension to DiDO, not a pivot**. Concretely: author one `dido-engagement` schema pack + one consulting skillpack, install them on the DiDO brain we already designed, and the retrieval engine, citations, dream cycle, multiplayer architecture (Supabase + `serve --http` + OAuth thin clients), the `source-mock` ingest CLI, and the Slack human-in-the-loop **all stay as-is**.

The work is therefore concentrated in three buckets, in rough order of difficulty:

1. **Ontology + importance model** (schema pack) — *small-to-medium, mostly declarative.*
2. **The 13 skills** (skillpack) — *medium; ~half are adaptations of existing GBrain skills, ~half are net-new.*
3. **Two genuinely novel/hard pieces** — the **pattern library** (`similar_to` / "what have we solved like this?") and **decision memory** as a first-class, enrichment-maintained object.

The one strategic tension to resolve early is **client confidentiality vs. DiDO's "everyone sees everything" thesis** (Section 13). It's the single thing most likely to force a structural decision rather than a declarative one.

My recommendation: **extend via packs, build in 4 phases, ship a thin vertical slice (ontology + 3 skills + decision memory) before committing to the full skill catalog and the pattern library.**

---

## 2. Background recap

**What DiDO already is.** A GBrain fork positioned as Sierra's *multiplayer company brain* (~25 people). The architecture is settled and well-documented: stateless processes over one Supabase Postgres+pgvector; git markdown repos as source of truth; each teammate is a thin OAuth-scoped MCP client (no central agent); a host-side dream/enrichment worker; ingest via a stdlib Python CLI (`source-mock/`) that POSTs clean markdown to `/ingest`; a Slack human-in-the-loop that fills gaps the brain can't. The hackathon brief already nominated **Decisions (+ rationale)** and **Blockers / open questions** as the two highest-value things to capture — which is exactly where the consulting ontology goes next.

**What the design doc proposes.** Re-point the brain from GBrain's investment-first default ontology (Company, Founder, Investor; `invested_in`, `founded`) to a consulting-first one centered on the **Client Engagement** (Client, Project, Deliverable, Decision, Risk, Opportunity, Expertise, Reusable Asset; `client_of`, `delivered`, `depends_on`, `similar_to`). Plus a new importance model (Tier 1/2/3 by ARR/renewal/risk instead of founder quality), ~13 consulting skills, and a "pattern library" so the brain answers *"what have we solved that looks like this?"* not just *"what do we know about Acme?"* The doc explicitly recommends a **layer, not a deep fork**.

**The key reframe (why this is mostly a configuration project, not a rewrite).** GBrain's schema-pack system (v0.39–v0.41) makes ontology a *dynamic, always-consulted artifact* every skill reads at runtime. A pack declares `page_types` (with `primitive`, `path_prefixes`, `extractable`, `expert_routing`, `aliases`), `link_types` (typed verbs between page types), `takes_kinds`, `filing_rules`, and `enrichable_types`. Packs `extend` a base pack, are version-pinned, are activated per-brain or per-source, and ship as tarballs through a publish-as-PR registry. Skills live in a parallel skillpack system. **This is a one-to-one home for every layer the doc lists.**

| Design doc's "layer" | Native GBrain home |
|---|---|
| Ontology (entities) | `page_types[]` in a schema pack |
| Relationship schema (edges) | `link_types[]` in a schema pack |
| Importance model | `expert_routing` flag + takes weights + an enrichment skill that recomputes tiers |
| Enrichment rules | the `enrich` skill + `enrichable_types` + filing rules |
| Skills | a `.gbrain-skillpack` |
| Cron jobs | the `cron-scheduler` skill + the dream cycle |

---

## 3. The core decision: extend via packs (recommended), pivot only if forced

**Recommended path — extend.** Author and install two artifacts on the existing DiDO brain:

- `dido-engagement` **schema pack** — `extends: gbrain-base`, overrides the active ontology and importance flags.
- `dido-consulting` **skillpack** — the 13 skills, several of which `borrow_from` existing GBrain skills.

Nothing in `gbrain/src/` changes for the common case. We activate the pack brain-wide (resolution tier 4, the DB config key) and iterate.

**Why this is preferable to a fork.** It preserves the ability to pull upstream GBrain improvements (the engine, retrieval, the dream cycle keep advancing), it keeps the multiplayer design doc valid unchanged, and it makes the consulting layer *itself* portable later if we ever do want to productize it.

**What would force a pivot (extend → modify the engine/core model).** Track these as explicit triggers; if we hit one, we stop and re-decide:

1. **Per-client confidentiality needs page-level ACLs.** GBrain's only isolation primitive is *source* scoping. If "Client A's team must not see Client B's engagement" requires finer-grained control than one-source-per-client gives us, that's an engine-level change (Section 13). **This is the most likely trigger.**
2. **Pattern matching needs typed cross-client retrieval the engine won't do.** If "similar_to" requires graph/vector behavior the current retrieval modes can't express, we'd extend retrieval (Section 12).
3. **Decision/contradiction reconciliation needs first-class temporal queries.** GBrain itself documents that "what was true last week but isn't now" + automatic contradiction reconciliation is "a different product class." If decision memory needs that natively, it's a build, not a config (Section 14).

None of these is certain; all are scoped below. The point: we go in via packs, and we have a named list of conditions that would justify going deeper.

---

## 4. What stays the same

Almost the entire DiDO build is reusable untouched.

| Component | Status under consulting extension |
|---|---|
| Retrieval engine (pgvector + keyword + RRF fusion, query expansion, backlink boost) | **Unchanged** |
| Citations / grounding (cited answers, `citation-fixer`) | **Unchanged** |
| Dream cycle (`runCycle`: synthesize, extract, consolidate, probe) | **Unchanged primitive**; we add consulting-specific enrich logic *as skills*, not new phases |
| Multiplayer architecture (Supabase, `serve --http`, OAuth 2.1, thin clients, no central agent) | **Unchanged** |
| Ingest pipeline (`source-mock/` CLI → `POST /ingest` → brain page) | **Unchanged transport**; we add an enrich step *after* ingest (Section 11) |
| Slack human-in-the-loop (gap → ask a human → write back → next dream cycle) | **Unchanged**, and *more* useful here (clients/decisions have human-only context) |
| Schema-pack + skillpack machinery (authoring, validation, distribution, audit) | **Unchanged** — it's the delivery vehicle |
| Markdown-in-git source of truth; Postgres as rebuildable cache | **Unchanged** |
| `compiled truth + dated timeline` page pattern (time awareness) | **Unchanged** — and it's exactly what decision memory needs |

The headline: **we are configuring and skinning a system we already stood up, not rebuilding it.**

---

## 5. What changes

| Area | Today (gbrain-base) | After |
|---|---|---|
| Active schema pack | `gbrain-base` (person/company/deal/meeting/concept/project…) | `dido-engagement` (client/engagement/deliverable/decision/risk/opportunity/asset…) |
| Primary object | Company / Person | **Client Engagement** |
| Importance / expert-routing | investment signals (founder quality, deal stage) | **client value, renewal proximity, delivery risk** |
| Fact extraction targets | MRR, raise, valuation | **ARR, renewal date, milestone dates, deliverable status, risk severity** |
| Filing rules | generic people/companies dirs | engagement-centric dirs (`clients/`, `engagements/`, `deliverables/`, `decisions/`, `risks/`) |
| Ingest post-step | "one file in → one page out" | + an **enrich pass** that writes Decision/Risk/Deliverable pages from raw artifacts |
| Default queries the brain is good at | "what do we know about X" | + "what's the account health," "why did we recommend X," "what have we solved like this" |

Crucially, these are **declarative or skill-level** changes. No retrieval, storage, or transport code changes for any row above except the ingest post-step (a new skill, not a transport change).

---

## 6. What's net-new

| New thing | Form | Difficulty |
|---|---|---|
| `dido-engagement` schema pack | YAML (page_types, link_types, flags, filing rules) | **S–M** (declarative; iteration on flags) |
| 13 consulting skills | markdown skillpack | **M** (≈7 adapt, ≈6 net-new) |
| Decision-memory enrich skill | skill + page template | **M** (structured page + timeline + sources) |
| Deliverable indexing | ingest/enrich skill + `deliverable` type | **M** (parse decks/memos → reusable pages) |
| Importance/tier recompute | cron skill that grades clients into tiers | **M** |
| **Pattern library (`similar_to`)** | link type + "Similar Client Finder" + "Case Study Generator" skills over vector search | **L** (the novel part) |
| Client-confidentiality model | source layout + scoping policy (or engine change) | **M–L** (decision-dependent — Section 13) |

---

## 7. Ontology in detail

Here's the design doc's ontology expressed as a concrete `dido-engagement` pack, adapted to a **studio** (Sierra) rather than a classic body-shop consultancy — e.g., Sierra may weight strategic/equity bets, not just billable ARR, so "importance" is parameterized, not hardcoded.

### Page types (entities)

| Type | primitive | path prefix | extractable | expert_routing | Notes |
|---|---|---|---|---|---|
| `client` | entity | `clients/` | yes | yes | the account; carries ARR, renewal date, sponsor |
| `engagement` | entity | `engagements/` | yes | yes | **the primary object**; replaces "company" as the gravity center |
| `stakeholder` | entity | `people/stakeholders/` | yes | yes | client-side people; sponsor flag drives importance |
| `deliverable` | annotation | `deliverables/` | yes | no | decks, memos, roadmaps → reusable knowledge |
| `decision` | temporal | `decisions/` | yes | no | structured recommendation + rationale + outcome |
| `risk` | temporal | `risks/` | yes | no | delivery/relationship risks; severity extracted |
| `opportunity` | temporal | `opportunities/` | yes | yes | renewals / expansions |
| `expertise` | concept | `expertise/` | yes | yes | what the firm knows; powers expert routing |
| `asset` | concept | `assets/` | yes | no | reusable templates/components/playbooks |
| `meeting` | temporal | `meetings/` | yes | no | inherited from base; links to engagement |

### Link types (relationships)

Mapping the doc's verbs directly:

| Verb | from → to |
|---|---|
| `client_of` | engagement → client |
| `owns` | engagement → deliverable / decision / risk |
| `requested` | stakeholder → deliverable / decision |
| `approved` | stakeholder → decision |
| `depends_on` | deliverable/decision → deliverable/decision |
| `blocked_by` | engagement/deliverable → risk |
| `delivered` | engagement → deliverable |
| `expert_in` | person → expertise |
| `similar_to` | engagement → engagement *(pattern library — Section 12)* |
| `renewal_for` / `expansion_for` | opportunity → client |

This is the bulk of the pack and it's **declarative YAML** — the worked `gbrain-recommended.yaml` in the fork is the template.

---

## 8. Importance model (Tier 1/2/3 → GBrain)

The doc's tiers map onto two GBrain mechanisms plus one new skill:

- **`expert_routing: true`** on `client`, `engagement`, `opportunity`, `stakeholder`, `expertise` makes them first-class in `whoknows` / `find_experts` (so the brain routes account questions to the right engagements/people, not raw text).
- **Takes weights + extracted facts** (`arr`, `renewal_date`, `delivery_risk`, `sponsor_active`) give the raw signals.
- **A new `account-health` cron skill** runs in the dream cycle, reads those facts, and writes a `tier` (1/2/3) onto each client/engagement page's compiled-truth block, with the timeline recording *why* the tier changed. Tiering becomes an auditable, time-aware fact — not a static label.

Tier inputs, per the doc, parameterized for Sierra: active executive sponsor, client value (ARR *or* strategic/equity weight), delivery risk, renewal within 90 days → Tier 1; active stakeholders / medium value / warm opportunities → Tier 2; historical contacts / one-offs → Tier 3.

---

## 9. The 13 skills

Each consulting skill maps to an existing GBrain skill it can `borrow_from`, or is net-new. This is what keeps the skillpack tractable.

| Consulting skill | Build | Borrows from / basis |
|---|---|---|
| Client Brief | adapt | `briefing`, `query` |
| Meeting Prep | adapt | `daily-task-prep`, `meeting-ingestion`, `briefing` |
| Executive Summary | adapt | `reports`, `query` |
| Risk Review | **new** | `signal-detector` (risk signals) + `reports` |
| Weekly Account Health | **new** | `cron-scheduler` + `reports` + the tiering skill (Section 8) |
| Opportunity Finder | **new** | `signal-detector` + graph traversal over `opportunity` |
| Proposal Writer | adapt | `query` + `reports` + asset reuse |
| Deliverable Reuse | **new** | `query` over `deliverable`/`asset` types |
| Case Study Generator | **new** | depends on pattern library (Section 12) |
| Expertise Mapper | adapt | `find_experts` / `whoknows` over `expertise` |
| Similar Client Finder | **new** | **the pattern library** (Section 12) |
| Decision Log | **new** | decision-memory enrich (Section 11) |
| Lessons Learned | adapt | `concept-synthesis`, `idea-lineage` |

Roughly **6 net-new, 7 adaptations.** The adaptations are mostly prompt + routing changes pointed at the new types; the net-new ones (especially the last three pattern-dependent skills) carry the real weight.

---

## 10. Decision memory + deliverable indexing

These are the two pieces that turn raw artifacts into structured, reusable knowledge — and they're where the hackathon's stated "Decisions + Blockers" intent becomes concrete.

**Decision memory.** Every significant recommendation becomes a `decision` page using GBrain's compiled-truth-+-timeline pattern: top section answers *why did we recommend this / who approved it / what alternatives existed*; the dated timeline records *what happened afterward*, with `sources` citations to the meeting/session it came from. Implemented as an **enrich skill** that fires during ingest/dream when a decision is detected. The timeline pattern means "why did we change our mind?" is *answerable from preserved history* — though turning that into a clean one-line answer is a skill we author, not a default (GBrain's temporal caveat, Section 14).

**Deliverable indexing.** Each deck/memo/roadmap becomes a `deliverable` page (extractable), linked to its engagement via `delivered`, tagged with the `expertise`/`asset` it embodies. That's what makes "Deliverable Reuse" and "Proposal Writer" real instead of a file search.

---

## 11. The pattern library (`similar_to`) — the hard, novel part

This is the doc's "compounding advantage": *"what have we solved that looks like this?"* It's the highest-value and highest-effort component, and it's where a pivot is most plausible.

**Approach that reuses the engine:** vector embeddings already exist on every page. "Similar Client Finder" / "Case Study Generator" become skills that (a) embed the current engagement's problem statement, (b) vector-search across `engagement`/`deliverable` pages, (c) materialize the strongest matches as `similar_to` links, and (d) synthesize a cited "here's what we did last time" answer. The `similar_to` edges accumulate over time, so the graph itself gets smarter — exactly the compounding the doc wants.

**Why it's L-sized / pivot-risk:** quality depends on retrieval tuning (which search mode, how to weight problem-shape vs. client identity), and on whether engagement pages carry a consistent enough "problem statement" structure to match on. If off-the-shelf vector search doesn't produce trustworthy matches, we'd invest in retrieval/structure — a deeper change. **Recommend prototyping this on real Sierra engagement data before committing to the two skills that depend on it.**

---

## 12. The strategic tension to resolve early: confidentiality vs. open visibility

DiDO's founding thesis is **democratized visibility — everyone can see everything, so anyone can function like a leader.** A client-engagement brain introduces the opposite pressure: **client confidentiality** (and sometimes internal-only commercial data like margins). These can conflict.

GBrain's *only* isolation primitive is **source scoping** (`--source` for write, `--federated-read` for read). So the realistic options:

1. **One source per client** (or per sensitivity tier), OAuth-scoped. Clean isolation, but cross-client pattern matching (Section 11) then has to cross sources — and the fork currently *rejects* multi-source queries when sources have divergent active packs (deferred to v0.40+). This collides head-on with the pattern library.
2. **One shared engagement source, open to all of Sierra**, matching DiDO's thesis. Simplest; assumes Sierra is comfortable with full internal transparency across all client work. For a 25-person studio this may be perfectly fine — but it's a *policy* call, not a technical default.
3. **Engine-level per-page ACLs.** The "real" answer for strict confidentiality, but it's the pivot trigger — net-new access-control work GBrain doesn't ship.

**This is the first thing I'd want your decision on**, because it determines whether the pattern library is cheap (option 2) or expensive (options 1/3), and whether we stay in "extend" or move toward "pivot."

---

## 13. Other risks & gaps

- **Temporal reconciliation is not free.** "What was true last week but isn't now" and automatic contradiction reconciliation are out-of-scope for GBrain by its own docs. We preserve the history; clean "why did we change our mind" answers are a skill we author. Scope it; don't overpromise.
- **Per-human identity / audit is weak.** Identity is per OAuth client, not per person; the audit trail is git history. For client work where "who approved this" matters, we may want per-human attribution sooner than the generic brain needed it.
- **Ingestion is DIY.** `/ingest` has no signature verification; pulling deliverables out of Drive/Slack/decks needs adapters. The `source-mock` CLI covers clean markdown; decks/PDFs need extraction.
- **Dreaming needs an always-on host.** Already flagged in the system-design doc; tiering + decision enrichment make a real host more important than it was for a demo.
- **Studio ≠ classic consultancy.** Sierra weights strategic/equity bets, not just billable ARR. The importance model must be parameterized (done in Section 8), and some doc assumptions (renewal probability, executive visibility) may need Sierra-specific definitions.

---

## 14. Phased roadmap + effort estimate

**Estimating basis (read before the numbers):** planning-grade T-shirt sizes, assuming **1–2 engineers already fluent in the DiDO fork**, the brain already provisioned (it is, per the system-design snapshot), and real Sierra engagement data available to test against. Ranges are wide on purpose; the pattern library and the confidentiality decision are the variance drivers. "wk" = person-week.

### Phase 0 — Decisions & data (prerequisite)
Resolve the confidentiality model (Section 12); confirm Sierra's importance definitions; assemble a real engagement dataset to test on. **~0.5–1 wk, mostly your input not engineering.**

### Phase 1 — Ontology slice (the foundation)
Author `dido-engagement` schema pack (page types, link types, flags, filing rules); activate on the brain; backfill/sync; validate routing with `whoknows`/`schema review-orphans`. **~1–2 wk. Size: M.**

### Phase 2 — Decision memory + 3 core skills (the first real value)
Decision-memory enrich skill + `decision`/`risk` page templates; deliverable indexing; ship **Client Brief, Decision Log, Weekly Account Health** (incl. the tiering cron skill). This is the smallest slice that demonstrably beats gbrain-base for Sierra. **~2–4 wk. Size: M–L.**

### Phase 3 — Full skill catalog
Remaining adaptations + net-new skills (Meeting Prep, Executive Summary, Risk Review, Opportunity Finder, Proposal Writer, Deliverable Reuse, Expertise Mapper, Lessons Learned). Largely parallelizable. **~3–5 wk. Size: L.**

### Phase 4 — Pattern library (the compounding moat)
`similar_to` mechanism + Similar Client Finder + Case Study Generator; retrieval tuning; prototype-first. **~3–6 wk, high variance. Size: L+.** *Gate on a successful prototype against real data before committing the full estimate.*

### Cross-cutting (spread across phases)
Ingest adapters for decks/PDFs (~1–2 wk), always-on host hardening (~0.5–1 wk), per-human identity if confidentiality demands it (**pivot-sized, separate estimate if triggered**).

**Rough total to the full vision (excluding a confidentiality pivot): ~10–18 person-weeks**, front-loaded so that *real value lands at the end of Phase 2 (~4–7 weeks in)*. If the confidentiality decision forces engine-level ACLs, add a separate pivot workstream we'd scope on its own.

---

## 15. Open questions for the next round

1. **Confidentiality model (Section 12)** — open-to-all-Sierra (cheap, matches DiDO's thesis) vs. per-client sources (isolation, but fights the pattern library) vs. per-page ACLs (pivot)? *This is the unlock for everything downstream.*
2. **Importance definition** — for a studio, is "client value" billable ARR, strategic weight, equity, or a blend? Who counts as an "executive sponsor"?
3. **Scope of "client"** — do we model only paying client engagements, or also internal Sierra projects/products under the same engagement ontology?
4. **Pattern library appetite** — is "what have we solved like this" a must-have (commit to Phase 4) or a nice-to-have we prototype and defer?
5. **Deliverable sources** — where do decks/memos actually live (Drive, Notion, Slack, local), so we can scope the ingest adapters?
