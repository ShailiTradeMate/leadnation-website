# VBIE Phase 5 — AI Brain + Verification + Trust Engine (Design)

> Architecture/algorithm design only. NO production code. Builds on frozen Phase-4 entity-centric model (GEID). Review before Phase 6.
> Brain is modular (5 brains, Phase 4 §2). This doc specifies each brain's internals, the scoring engines, and AI-agent readiness.

---

## §1. Brain contract (all 5 brains)
Grounded-only (graph + provenance, never open web) · candidate-gated (nothing unverified goes live) · every decision → `brain_logs` (inputs + method + evidence + confidence + rationale, permanent) · reversible mutations · human-QA hook for mid-confidence · uses **Emergent LLM key** for LLM steps · answers cached in `brain_cache`.

---

## §2. Collection Brain (what/when to ingest)
- **Inputs:** `sources` (reliability, cadence), coverage gaps (buyers/country vs target), corridor priorities.
- **Logic:** score each source run by `priority = source.buyer_yield × source.reliability × staleness × corridor_value`; schedule due connectors; route unstructured inputs to AI extraction; propose *new* candidate sources (agent-style) → human review.
- **Output:** nightly ingestion plan; candidates (Tier 0).
- **MVP:** rules-based prioritization.

## §3. Verification Brain (is it real, active, reachable, safe?)
### §3.1 Checks → verification_logs
| Dimension | Method | Evidence |
|-----------|--------|----------|
| Existence | registry match (Companies House/Sirene/gBizINFO/ABN/ACRA/GEID resolve) | registry record |
| Trade activity | ≥1 customs/BoL/tender/CID record; HS/corridor match | shipment/tender ref |
| Recency | latest signal age | signal ts |
| Reachability | domain live + MX + email verify + phone | verifier results |
| Corroboration | # independent source categories agreeing | provenance set |
| **Risk gate** | sanctions/PEP screen (OFAC/EU/UN/UK + trade.gov CSL) | screening result |
### §3.2 Tier assignment
Tier 0 (candidate) → 1 (registry) → 2 (registry+trade) → 3 (+contact) → 4 (multi-source+fresh+clean, "LeadNation Verified™"). **Only Tier ≥2 becomes visible.** Sanctions hit → hard suppress regardless.

## §4. Matching Brain (entity resolution + relationship inference)
- **Resolution** (Phase 3 §5): normalize → block → pairwise score → decide (auto-merge on strong key / merge / QA / distinct) → reversible merge → GEID survives.
- **Relationship inference:** from shipments/tenders/registry → emit `relationships` edges (`imports_from`, `trades_with`, `corridor`, `deals_in`, `classified_as`) with **weight + confidence + strength_meta** (#2,#9). Edges are versioned (`valid_from/valid_to`, never deleted, #5).
- **Onboarding dedupe:** on user sign-up, run match against `entities` by domain/name/registry → surface claim candidates (Networking requirement).
- **MVP:** rules→ML; edges populated but traversal UI post-MVP.

## §5. Recommendation Brain (POST-MVP)
- Query-time ranking = `Trust × corridor relevance × recency × verification tier`.
- **Exporter↔Buyer AI Match Score** (deferred): HS overlap × corridor × import volume/frequency × recency × trust × risk → 0–100 + grounded explanation.
- Cross-sell via Industry Relationship Graph (#8). **Excluded from MVP.**

## §6. Explanation Brain (grounded summaries + "why")
- **Input:** entity attributes + `provenance` + `brain_logs`.
- **Output:** AI Summary (every sentence maps to a provenance ref; unsupported → dropped) + "why shown / why trusted" for the Buyer Card. Cached in `brain_cache`.
- **Anti-hallucination:** RAG over the entity record only; no external recall; confidence labels surfaced; never invents contacts.

---

## §7. Scoring engines (algorithms)

### §7.1 Confidence Score (per attribute → entity rollup) [#3]
`attr_confidence = source_reliability × recency_factor × corroboration_factor`
- `recency_factor = 0.5^(age_months / 12)`
- `corroboration_factor = 1 − 0.6^(independent_sources)` (more independent sources → →1)
- `entity.confidence_score = weighted mean of key-attribute confidences`.

### §7.2 Freshness Score [#7]
`freshness = 100 × 0.5^(median_attr_age_months / 12)` → silent entities decay; triggers re-verification when below threshold.

### §7.3 Source Reliability Score [#6]
`reliability = w1·accuracy_vs_corroborated + w2·uptime + w3·(1−wrong_feedback_rate) + w4·freshness_of_feed`, seeded from prior `trust_weight` (official>licensed>crawled), learned nightly; history in `sources.reliability_history`.

### §7.4 Trust Score (composite) — the headline number
`Trust = (0.25·Identity + 0.25·TradeEvidence + 0.20·Recency + 0.15·Corroboration + 0.10·Reachability + 0.05·Standing) × RiskGate`
- Sub-scores derive from confidence + verification results; `RiskGate ∈ {0..1}` (sanctions/dissolved crush it).
- Bands: 90+ Platinum · 75–89 Verified · 50–74 Probable · 25–49 Weak · <25/gated.
- **Recompute triggers:** new signal, nightly decay, feedback, sanctions update. Each recompute → `score_history` (#3) + `brain_logs`.
- **Calibration:** back-test Trust bands vs. deliverability/conversion; tune weights.

### §7.5 Relationship strength [#2/#9]
`edge.weight = f(frequency, recency, volume, source_count)`; `edge.confidence = evidence certainty`; `strength_meta` stores components → powers graph ranking later.

---

## §8. Brain orchestration (nightly + query-time)
Nightly: **Collection → (AI extract) → Matching → Verification → Trust/scores → Explanation → cache**. Query-time: **Recommendation** (ranking; match post-MVP). Each brain is an independently scalable service behind the single Brain API (shared web+app).

## §9. AI Agent readiness [#10]
- **Tool interface over the graph:** read tools (`get_entity(geid)`, `search`, `traverse`, `get_evidence`) + propose tools (`suggest_merge`, `suggest_edge`, `suggest_source`).
- **Guardrails:** agents *propose* → candidate/QA queue; **never auto-mutate** the live graph. Memory via `brain_logs` (#4) + `brain_cache` (#7).
- MVP: interface reserved; agents inactive.

## §10. MVP vs later
**MVP active:** Collection(rules), Verification(+sanctions gate), Matching(rules), Explanation(grounded); Trust v0 + Confidence + Freshness + SourceReliability(lite); brain_logs + brain_cache(lite).
**Later:** Recommendation Brain + AI Match Score, ML matcher, agentic discovery, full graph traversal ranking.

---

## §11. Phase 5 — Review gate (approve → Phase 6: Website + Mobile App Integration)
1. 5-brain internals + contracts — approved?
2. Verification tiers + mandatory sanctions gate — approved?
3. Scoring algorithms (Trust/Confidence/Freshness/Source-Reliability formulas) — approved to prototype/calibrate?
4. Explanation Brain grounded/anti-hallucination rules — approved?
5. AI-agent readiness (propose-not-mutate) — approved as READY (inactive MVP)?
6. Recommendation Brain + AI Match Score deferred to post-MVP — confirmed?

Discipline maintained: **Research → Design → (this) Review → Approval → Implementation.** No production code until the full phase set is approved.
