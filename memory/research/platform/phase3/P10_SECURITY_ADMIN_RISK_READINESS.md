# VBIE Phase 3 — Doc 6/6: Shared Architecture · Security · Admin · Risk · Implementation Readiness
## (Section 8 · Section 10 · Section 11 · Deliverable 9: Risk Analysis · Deliverable 10: Implementation Readiness Report)

> Architecture only. NO code. Closes Phase 3.

---

## SECTION 8 — SHARED ARCHITECTURE (one source of truth)
Reaffirmed for the ingestion plane: connectors write to the **same** Buyer Graph the web + app read from. There is exactly **ONE** of each:
| Backend | MongoDB | Firebase | Customer ID | Buyer ID | Trust Engine | Brain | Search API | Verification API | Source Registry | Intelligence DB |
Ingestion never creates a parallel store; it only enriches the single graph. Web/app remain thin clients. Firebase/Mongo shared with the DigitalOcean identity backend → **reuse, never fork** (handoff rule).

---

## SECTION 10 — SECURITY
| Control | Design |
|---------|--------|
| **Crawler isolation** | Ingestion plane runs in a network-segmented worker tier; no inbound from internet; egress-only; cannot reach auth/customer collections directly (write via validated service) |
| **API secrets** | All source keys in env/secret manager, referenced by `sources` registry via SecretResolver; never in code, DB, or `.env` committed; rotation supported |
| **Rate limits** | Per-domain + per-provider quotas enforced; global concurrency caps; protects sources & our IP reputation |
| **Audit logs** | Immutable `raw_records`, `provenance`, `match_decisions`, `access_log`, `connector_runs`; who/what/when for every read & mutation |
| **Source authentication** | OAuth/API-key/token per source; least-privilege; per-source credential scoping |
| **Data encryption** | TLS in transit; encryption at rest (Atlas); **personal `contacts` collection separately encrypted** + geo-partitioned (EU) |
| **Abuse prevention** | Legal Gate blocks forbidden/gated targets; robots/ToS enforcement; anomaly detection on connector behavior; kill-switch per source |
| **API quotas** | Public/customer API rate-limited per Customer ID; tiered quotas; abuse throttling |
| **PII governance** | Lawful-basis stamp required; DSAR/erasure workflow; opt-out/suppression applied every refresh |

---

## SECTION 11 — ADMIN DASHBOARD
Single admin surface (shared backend) exposing:
| Panel | Shows |
|-------|-------|
| Connector dashboard | Each connector: status, last run, throughput, error rate, quota usage |
| Crawler health | Frontier size, fetch success %, 429/403 rates, per-domain politeness state |
| Failed jobs / retry queue | Dead-letter items, retry counts, manual requeue |
| Country coverage | Buyers per country vs target; free-vs-licensed mix |
| Source coverage | Buyers per source; buyer_yield realized; stale sources |
| Buyer acquisition metrics | New Tier-2+ buyers/night, corroboration depth, contactability |
| Data freshness | Median attribute age; % refreshed on SLA |
| Legal alerts | New forbidden/ToS changes; sources needing legal review; suppression events |
| License expiry | Commercial provider contracts, renewal dates, usage vs cap |
| QA queue | Mid-confidence merges + Tier-4 promotions awaiting human review |
| Trust calibration | Trust band vs actual deliverability/conversion |

---

## DELIVERABLE 9 — RISK ANALYSIS
| # | Risk | Likelihood | Impact | Mitigation |
|---|------|:--:|:--:|-----------|
| R1 | GDPR/DPDP breach on personal data | Med | High | Gated `contacts`, lawful-basis engine, DSAR/opt-out, EU geo-partition, minimize personal fields |
| R2 | ToS violation / crawler blocked | Med | Med | Legal Gate + allowlist + robots/ToS review; API/bulk first; partnerships for directories |
| R3 | Source schema/endpoint changes break connector | High | Med | Connector versioning, schema validation, health checks, auto-alert + retry; failure isolation |
| R4 | Licensed-data redistribution overreach | Low | High | License Registry (field-level terms), evidence-of-existence display, no verbatim resale |
| R5 | AI hallucination into live graph | Med | High | Candidate-gate, snippet-backed extraction, schema validation, human QA, grounded-only Brain |
| R6 | Bad entity merges (false positives) | Med | Med | Strong-key auto-merge only; mid-band → human QA; reversible merges; feedback loop |
| R7 | Data staleness perceived as inaccuracy | Med | Med | Freshness SLA + "last verified" on every attribute; nightly decay |
| R8 | India mirror T2 truncation / feed changes | Med | Med | Provider-agnostic; diversify corridors; don't hard-depend on one feed |
| R9 | Cost overrun (LLM/verification/proxies) | Med | Med | Structure-first parsing, nightly caps, free-first, cost guardrails |
| R10 | Sanctioned entity surfaced | Low | High | Mandatory daily sanctions gate before promotion; hard suppress |
| R11 | Secret leakage | Low | High | Secret manager, rotation, network isolation, audit |
| R12 | Scaling debt | Low | Med | Lean-now/scale-ready architecture; shard/stream only when metrics demand |

---

## DELIVERABLE 10 — IMPLEMENTATION READINESS REPORT

### §10.1 Is the Phase-3 blueprint ready to implement?
**YES — the connector/crawler/ingestion architecture is implementation-ready**, conditional on the pre-build checklist below. It is legal (Legal Gate + `sources` policy), scalable (queue + shard + incremental), provider-agnostic (adapter registry), country-agnostic (add-source-not-architecture), AI-ready (grounded extraction + resolution), evidence-driven (no field without provenance), and startup-friendly (free-first, lean-now).

### §10.2 Readiness scorecard
| Dimension | Status |
|-----------|:--:|
| Legally compliant | ✅ (gate + registry + gated PII + sanctions) |
| Commercially reusable | ✅ (open/licensed handled per policy) |
| Scalable (10K→10M) | ✅ (staged) |
| Startup friendly / cost efficient | ✅ (free-first, caps, lean infra) |
| AI ready | ✅ (extraction + resolution + grounded Brain) |
| Evidence driven | ✅ (Evidence Engine mandatory) |
| Provider/country agnostic | ✅ (adapters + registry) |
| Shared web+app | ✅ (one backend/DB/Brain) |

### §10.3 Pre-build checklist (must be true before Phase-implementation code)
- [ ] `sources_seed.json` legal-reviewed per source (verdict/license/attribution/personal) — **draft done**.
- [ ] Legal Gate policy table per country (GDPR/DPDP/FOIA/open) finalized.
- [ ] Lawful-basis engine + LIA templates + DSAR/opt-out workflow specified.
- [ ] Secret manager + per-source credential provisioning ready (env-only).
- [ ] MongoDB collection schemas + indexes finalized (**Phase 4**).
- [ ] Brain resolution/scoring algorithms specified (**Phase 5**).
- [ ] Connector adapter registry + factory interface signed off.
- [ ] Admin dashboard scope confirmed.
- [ ] Confirm reuse of shared Firebase/Mongo/Customer IDs (no fork).

### §10.4 Recommended build order (when approved)
1. Foundations: `sources` registry loader + Legal Gate + Provenance write-path + secret resolver.
2. 3 free connectors first (GovernmentAPI: Companies House/SAM.gov/Comtrade) + CSV (Canada CID) + CBP BoL.
3. Entity resolution v1 (rules) + Verification + Trust v0 + sanctions gate.
4. Nightly orchestrator v0 (single broker, batch).
5. Buyer Card + Source Evidence + Search API (web+app).
6. Claim-this-Company. Then licensed adapters + AI extraction depth + scaling.

### §10.5 Verdict
**Phase 3 blueprint APPROVED-READY pending Phase 4 (DB schemas) + Phase 5 (Brain) design.** No blocker. Discipline maintained: **Research → Design → (this) Review → Approval → Implementation.**

---

## Phase 3 — Review gate
Please confirm to proceed to **Phase 4 (Unified Buyer Intelligence Database — final collection schemas & indexes)**:
1. Connector framework + typed connectors + adapter registry — approved?
2. Smart Crawler design (Legal Gate, delta/hash, structure-first, AI-fallback) — approved?
3. Evidence Engine (no field without provenance; write-path enforced) — approved?
4. Orchestration + queue + scaling (lean-now, scale-ready) — approved?
5. Security + Admin scope — approved?
6. Any source to add/remove in the Country/Source matrices before we freeze the registry?
