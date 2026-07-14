# VBIE Phase 4 — Doc 2/2: Knowledge-Graph Readiness · Brain Modularization · Explainability · Review
## (incorporates additions #2 #4 #5 #8 #9 #10 · evolution to Global Trade Knowledge Graph)

> Architecture only. NO code. Closes Phase 4.

---

## §1. Knowledge Graph readiness (#5) — evolution path, not a rewrite
The Global Trade Knowledge Graph (GTKG) is a **projection** of Phase-4 collections. We build KG-ready from day one, activate later.

### §1.1 Node & edge model (already in the DB)
| Node type | Backed by | Example edges |
|-----------|-----------|---------------|
| Entity (buyer/supplier/agency/mfr) | `buyers`/`companies` | trades_with, imports_from, subsidiary_of, same_group, member_of |
| Product (HS) | `products` | deals_in, classified_as(industry) |
| Industry | `industries` | industry_related, industry↔HS |
| Country | `countries` | corridor(country→country), operates_in |
| Trade Event | `trade_events` | exhibited_at, attended, awarded_at |
| Person (gated) | `contacts` | works_at (consent/lawful basis only) |

### §1.2 Three graph capabilities, staged
- **Relationship Graph (#2)** — buyer↔supplier↔corridor edges. *Ready in schema; populated as shipments/tenders accrue; traversal UI post-MVP.*
- **Industry Relationship Graph (#8)** — HS↔industry + industry co-occurrence (buyers importing HS-A also import HS-B). *Enables "related industries / cross-sell corridors".*
- **Country Intelligence relationships (#9)** — corridor edges + country↔HS strengths (which countries buy which HS). *Powers market-selection intelligence + corridor sizing (fed by UN Comtrade).*

### §1.3 Export path
Nightly (or on-demand) projection job mirrors `buyers`+`relationships`+node collections into a native graph DB (Neo4j/Neptune) when traversal scale demands it. Mongo remains source of truth; graph DB is a read-optimized replica. **Zero remodeling** — edges already exist.

---

## §2. Brain modularization (#10) — 5 brains, one decision log
The Brain is split into **5 cooperating modules**, each with a clear contract; all write explainable records to `brain_logs` (`brain_type` field). Modular = independently scalable, testable, and activatable.

| Brain | Responsibility | Reads | Writes | MVP |
|-------|----------------|-------|--------|:--:|
| **Collection Brain** | Decide what/when to ingest; source prioritization; discover new sources; route AI extraction | `sources`(reliability), coverage gaps | ingestion plan, candidates | ✅ (rules) |
| **Verification Brain** | Existence/trade/reachability checks; sanctions gate; assign verification tier | candidates, registries, screening | `verification_logs`, tier | ✅ |
| **Matching Brain** | Entity resolution (dedupe/merge); relationship-edge inference | candidates, `buyers`, `relationships` | `match_decisions`, edges | ✅ (rules→ML) |
| **Recommendation Brain** | Ranking; (post-MVP) exporter↔buyer AI Match Score; cross-sell via industry graph | `buyers`, graph, Trust | ranked results, match scores | ⏸ **post-MVP** |
| **Explanation Brain** | Grounded natural-language summaries + "why shown / why trusted" | entity + `provenance` | AI summary, explanations | ✅ |

### §2.1 Brain orchestration
Nightly orchestrator invokes brains in order: **Collection → (extract) → Matching → Verification → (Trust) → Explanation**; Recommendation runs at query-time (and post-MVP for match). Each brain is a service behind the single Brain API (shared by web+app).

### §2.2 Shared guardrails (all brains)
Grounded-only (graph + provenance, never open web) · candidate-gated · every decision logged with inputs+rationale+evidence+confidence · reversible where mutating · human-QA hook for mid-confidence.

---

## §3. AI Explainability (#4) — `brain_logs`
```
brain_logs {
  _id, brain_type: "collection|verification|matching|recommendation|explanation",
  subject: {node_type, id}, action: "merge|reject|verify|score|rank|summarize|ingest",
  inputs: {...signals/attributes used...},
  method: "rule:<id> | model:<name>@<ver>",
  decision, confidence,
  evidence: [provenance_ref],        # what facts justified it
  rationale_text,                    # human-readable "why"
  reversible: bool, ts
}
```
- **Every** buyer display, merge, score change, and summary is traceable to a `brain_logs` entry → answers "why is this buyer here / why this Trust / why merged".
- Powers Buyer Card "AI Summary" + "why trusted" tooltip; powers admin QA; satisfies "no hallucinations — everything cited".

---

## §4. How the 10 additions map to the DB (checklist)
| # | Addition | Where | MVP |
|---|----------|-------|:--:|
| 1 | Company Timeline | `company_timeline` (derived) | ✅ lite |
| 2 | Relationship Graph readiness | `relationships` edges | READY |
| 3 | Confidence Score | per-attribute + `buyers.confidence_score` | ✅ |
| 4 | AI Explainability | `brain_logs` | ✅ |
| 5 | Knowledge Graph readiness | node+edge collections + export projection | READY |
| 6 | Source Reliability Score | `sources.reliability_score` | ✅ lite |
| 7 | Buyer Freshness Score | `buyers.freshness_score` | ✅ |
| 8 | Industry Relationship Graph | `industries` + edges | READY |
| 9 | Country Intelligence relationships | `countries` + corridor edges | READY |
| 10 | Brain modularization (5 brains) | `brain_logs.brain_type` + service split | ✅ (Rec Brain post-MVP) |

---

## §5. Startup-friendly ↔ future-proof balance
- **Runs lean now:** single Atlas cluster, MVP-active collections only, rules-based brains, nightly batch. The READY collections cost ~nothing empty.
- **Evolves seamlessly:** activate edges → Relationship/Industry/Country graphs; project → native graph DB; turn on Recommendation Brain → AI Match Score; enable `entity_versions` → full time-travel. No migrations that break existing data (append-only, provenance-preserving).
- **One source of truth preserved** throughout (web+app+brains share the same graph).

---

## §6. Data-integrity rules (enforced)
1. No attribute without provenance (write-path reject).
2. No edge without evidence.
3. No personal data without lawful basis.
4. No visible buyer below Tier 2 or failing sanctions gate.
5. Merges reversible; versions append-only.
6. Every score recomputable from stored inputs (auditable).

---

## §7. Phase 4 — Review gate (approve to proceed to Phase 5: AI Brain + Verification + Trust Engine)
Please confirm:
1. **Collection set** (MVP-active vs READY-dormant split) — approved?
2. **Graph-native-in-Mongo** model with later projection to a native graph DB — approved?
3. **Four scores** (Trust, Confidence, Freshness, Source Reliability) on the schema — approved?
4. **5-Brain modularization** with Recommendation Brain deferred to post-MVP — approved?
5. **`brain_logs` explainability** as the single decision ledger — approved?
6. Any collection/field to add before we **freeze the data model** and move to Phase 5?

Discipline maintained: **Research → Design → (this) Review → Approval → Implementation.** No production code will be written until the full phase set is approved.
