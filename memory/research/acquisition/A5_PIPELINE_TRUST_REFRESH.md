# Deliverables 9, 10, 11 — AI Verification Pipeline + Trust Score Integration + Refresh Strategy

---

## Deliverable 9 — AI VERIFICATION PIPELINE (the "smarter every night" engine)

### §1. Improved pipeline (upgrades the linear diagram you proposed)
Your proposed flow was linear (sources → ... → trust → DB). The improved design is a **staged pipeline with feedback loops, a candidate quarantine, and a nightly orchestrator** — so nothing unverified reaches the product, and the system self-improves.

```
                    ┌───────────────── NIGHTLY ORCHESTRATOR (scheduler) ─────────────────┐
                    ▼                                                                     │
[1] INGEST (connectors: gov APIs · registries · customs/BoL · tenders · trade news/RSS · │
            expo lists · embassies/councils · licensed feeds)                            │
   → raw_records (immutable, provenance-stamped, personal-data flagged)                  │
                    ▼                                                                     │
[2] NORMALIZE (canonical schema · HS harmonization · address/name cleansing ·           │
              LLM extraction for unstructured news/PDF → structured candidates)          │
                    ▼                                                                     │
[3] CANDIDATE QUARANTINE (Tier 0) — nothing here is shown to users                       │
                    ▼                                                                     │
[4] ENTITY RESOLUTION (block → match → merge; strong keys reg_id/VIES/domain + ML fuzzy) │
                    ▼                                                                     │
[5] AI VERIFICATION                                                                      │
     ├ Existence   : registry match (Companies House/Sirene/gBizINFO/ABN/...)            │
     ├ Trade proof : ≥1 customs/BoL/tender record, HS/corridor match                     │
     ├ Reachability: domain live + MX + email verify (ZeroBounce/NeverBounce) + phone    │
     ├ Corroboration: count independent source categories                                │
     ├ LLM cross-check: reconcile conflicting facts, flag anomalies (with evidence)      │
     └ SANCTIONS/PEP GATE: OFAC/EU/UN/UK + trade.gov CSL (hard fail → suppress)          │
                    ▼                                                                     │
[6] DEDUPLICATION pass (post-verify merge of newly-linked entities)                      │
                    ▼                                                                     │
[7] TRUST SCORING (factor model + decay + risk multiplier) → tier assignment             │
                    ▼                                                                     │
[8] PROMOTION GATE: Tier ≥2 → LeadNation DB (visible); else stay Tier 0/1 (internal)     │
                    ▼                                                                     │
[9] LeadNation Buyer Graph  →  Product / Trust API / AEO pages / Intent alerts           │
                    │                                                                     │
                    └──── FEEDBACK LOOPS ────────────────────────────────────────────────┘
   (user "bad data" reports · deliverability results · buyer self-claim · QA sampling)
                     → adjust confidences, re-verify, improve matching model
```

### §2. Why each upgrade matters
- **Candidate quarantine (Tier 0):** competitors show unverified rows as buyers; LeadNation never does — quarantine enforces this.
- **Sanctions gate inside verification:** compliance can't be an afterthought.
- **LLM cross-check with evidence:** AI *assists* verification (reconciles conflicts, extracts from news) but never auto-trusts — every AI claim needs corroboration + stored evidence.
- **Feedback loops:** real-world outcomes (bounces, user reports, self-claims) continuously retrain matching + recalibrate Trust → genuinely "smarter every night."
- **Nightly orchestrator:** autonomous; improves DB without users creating accounts (end-goal requirement).

### §3. AI/ML components (use Emergent LLM key where LLM needed)
- **Entity matching model** (start rules/heuristics → graduate to ML classifier on labeled merges).
- **LLM extractor** for unstructured sources → structured candidate events (with source snippet).
- **LLM reconciler** for conflicting attributes + anomaly flags.
- **Deliverability + phone validators** (3rd-party APIs).
- **Calibration monitor** comparing Trust bands to actual outcomes.

---

## Deliverable 10 — TRUST SCORE INTEGRATION
(Full model in `/app/memory/research/05_TRUST_AND_VERIFICATION.md`; here is how it *plugs into acquisition*.)

- **Computed at pipeline stage [7]**, stored on `entities.trust_score/trust_band/verification_tier`.
- **Gates promotion (stage [8]):** only Tier ≥2 (registry+trade verified) becomes visible; Tier 4 = "LeadNation Verified™" premium.
- **Drives ranking:** discovery results ordered by Trust × corridor relevance × recency.
- **Recompute triggers:** new signal, refresh cycle, feedback, sanctions update (see Refresh).
- **Explainability payload** rendered on every buyer (identity/trade/recency/corroboration/reach/standing + risk gate + provenance) → the citable AEO asset.
- **Factor weights (start):** Identity 25 · Trade 25 · Recency 20 · Corroboration 15 · Reachability 10 · Standing 5 · Risk gate ×0–1. Back-test & tune against deliverability/conversion.

---

## Deliverable 11 — REFRESH STRATEGY
| Source class | Cadence | Mechanism |
|--------------|---------|-----------|
| Sanctions / screening lists | **Daily (real-time on publish)** | Re-screen all visible entities; instant suppress on hit |
| Procurement / tenders | **Daily** | Incremental API pulls (TED/SAM/UNGM) → new IntentEvents |
| Trade news / RSS | **Daily / hourly** | RSS + sitemaps → LLM extraction |
| Shipment / BoL (US CBP + licensed) | **Weekly** | Vendor update cycle; new consignees → candidates |
| Company registries | **Weekly–monthly** (event-stream where available, e.g. Companies House stream) | Status/officer/address changes → Trust recompute |
| Trade statistics | **Monthly** | Comtrade/national releases → corridor validation |
| Contact/web enrichment | **Monthly + on-access** | Re-verify email/phone (decay ~30%/yr) |
| Expo/exhibitor lists | **Per event calendar** | Organizer feed/partnership |
| Full graph re-score | **Nightly** | Apply time-decay, recompute Trust, demote dormant |

**Refresh principles:** incremental (only changed records), idempotent, provenance-appending (never destructive), and always re-applying the suppression/opt-out registry. Every refresh updates `last_verified` and can only *raise* or *lower* Trust with evidence — never silently.

### Nightly job sequence (orchestrator)
1. Pull incremental deltas (tenders, news, registry streams).
2. Refresh due shipment/registry batches.
3. Re-screen sanctions on all visible entities.
4. Re-resolve new candidates; re-verify due entities.
5. Recompute Trust + apply decay; promote/demote across tiers.
6. Emit intent alerts for watched corridors/buyers.
7. Write calibration + acquisition KPIs to a dashboard.
