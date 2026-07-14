# Phases 5, 6, 7 — Shared Platform · Buyer Intelligence Card · Nightly Orchestrator

---

# PHASE 5 — WEBSITE + APP: ONE SOURCE OF TRUTH

## §5.1 Shared-architecture principle
Website (React) and Mobile App (React Native / Expo) are **thin clients** over a **single shared backend**. Nothing about buyer data, trust, or auth is duplicated client-side.

```
        ┌───────────────┐        ┌────────────────────┐
        │  Website (React) │      │ Mobile App (Expo)  │
        └───────┬─────────┘      └─────────┬──────────┘
                └───────────────┬───────────┘
                                ▼
                 ┌──────────────────────────────────┐
                 │  SHARED FastAPI Backend (/api/*)  │
                 │  Auth · Customer IDs · Brain ·    │
                 │  Buyer DB · Search · Verification │
                 │  · Trust Score APIs               │
                 └───────────────┬──────────────────┘
                    ┌────────────┼─────────────┐
                    ▼            ▼             ▼
              MongoDB Atlas   Firebase Auth   Brain service
              (Buyer Graph)   (identity)      (intelligence)
```

## §5.2 Shared components (must NOT be duplicated)
| Shared asset | Rule |
|--------------|------|
| Backend (FastAPI) | Single deployment; all `/api/*` routes serve both clients |
| MongoDB Atlas | One Buyer Graph; no per-client DB |
| Firebase Auth | One identity project (already shared per handoff — **do not fork**) |
| Customer IDs | One customer record used across web + app |
| Brain | One intelligence service (merge/score/summarize) |
| Buyer Database | One canonical `entities` graph |
| Search / Verification / Trust APIs | One API surface; clients differ only in presentation |

## §5.3 Practical rules (fits existing LeadNation stack)
- Clients call `REACT_APP_BACKEND_URL` (web) / configured base URL (app) → same `/api` gateway.
- No business logic (trust, merge, ranking) in clients — all server-side.
- Feature parity via shared API; UI adapts to form factor only.
- **⚠️ Shared-infra warning (from handoff):** MongoDB + Firebase are shared with the DigitalOcean identity backend — reuse identity, never duplicate or mutate auth logic.

---

# PHASE 6 — BUYER INTELLIGENCE CARD (what users actually see)

Not a company name — an **evidence-backed intelligence object.** Every field is provenance-linked.

## §6.1 Card anatomy
```
┌─────────────────────────────────────────────────────────────┐
│ ACME PHARMA INC.                            🛡 Trust 87 / Verified │
│ 🇺🇸 United States · Pharmaceuticals · [Tier 3: Contact-verified]  │
├─────────────────────────────────────────────────────────────┤
│ Website  acmepharma.com ✓ (live, MX valid)                    │
│ Industry Pharmaceutical distribution (NAICS 424210)           │
│ Products HS 3004 (medicaments), HS 3002 (blood products)      │
│ Import Activity  ▇▇▇▅▂  6 shipments · last 2026-04 · from IN,DE │
│ Govt Registration  SAM.gov UEI ABC123 · state reg #01234567    │
│ Trust Score  87  [Identity 92 · Trade 85 · Recency 78 ...]    │
│ Verification Level  Tier 3 (registry + trade + contact)       │
│ Risk Flags  ✅ No sanctions/PEP hits (screened 2026-06-01)     │
│ AI Summary  "Active US pharma importer sourcing medicaments   │
│   from India & Germany; 6 verified ocean shipments since 2024;│
│   registered federal contractor; reachable via verified domain."│
│   [every sentence links to a source]                          │
├─────────────────────────────────────────────────────────────┤
│ EVIDENCE & SOURCES (12)                          Last updated  │
│  • US CBP ocean BoL — 2026-04-12  [view]         2026-06-01    │
│  • SAM.gov Entity API — 2026-05-20 [view]                     │
│  • Company website — 2026-05-28 [view]                         │
│ VERIFICATION TIMELINE                                          │
│  2024-06 first seen → 2024-06 registry-verified →             │
│  2025-01 trade-verified → 2026-05 contact-verified            │
└─────────────────────────────────────────────────────────────┘
```

## §6.2 Field → source → policy mapping
| Card field | Source(s) | Display policy |
|------------|-----------|----------------|
| Company Name | Registry | Public |
| Country | Registry/customs | Public |
| Website | Company site verify | Public |
| Industry | Registry/NAICS/JSIC | Public |
| Products (HS) | BoL/customs/tender | Public |
| Import Activity | Public BoL + licensed mirror | Public (aggregated); licensed rows shown as evidence-of-existence |
| Govt Registration | Registry/SAM/IEC | Public (non-personal) |
| Trust Score | Brain | Public + breakdown |
| Verification Level | Pipeline tier | Public |
| Evidence / Sources | Provenance ledger | Public (with attribution) |
| Last Updated | refresh_log | Public |
| Risk Flags | Sanctions screening | Public (compliance) |
| AI Summary | Brain (grounded) | Public; citation-bound |
| Verification Timeline | signals/refresh_log | Public |
| **Personal contacts** (email/phone/person) | gated | **Behind auth + lawful-basis + opt-out; NOT on public pages** |

**Key UX differentiator:** the "Evidence & Sources" panel and Verification Timeline are the trust moat — no competitor shows *why* to believe a buyer is real.

---

# PHASE 7 — NIGHTLY ORCHESTRATOR

Autonomous job that makes the DB "smarter every night" **without users creating accounts.** Full pipeline in `A5_PIPELINE_TRUST_REFRESH.md`; here is the operational job design.

## §7.1 Nightly job DAG
```
00:00  DISCOVER   → pull deltas: new tenders (TED/SAM/UNGM), trade news RSS,
                    new BoL consignees, new registry incorporations → candidates(Tier 0)
01:00  REFRESH    → re-pull due registry/shipment batches; update changed fields
02:00  VALIDATE   → website liveness + MX; email re-verify (decayed); phone check
02:30  SANCTIONS  → re-screen ALL visible entities (OFAC/EU/UN/UK + trade.gov CSL)
03:00  RESOLVE    → entity resolution on candidates; merge duplicates (log decisions)
04:00  SCORE      → recompute Trust (apply decay); reassign tiers; promote/demote
04:30  CLEANUP    → dormant(18–24mo)→hide; dissolved→archive; expire stale personal data
05:00  SUMMARIZE  → Brain regenerates AI summaries for changed entities (grounded)
05:30  ALERTS     → emit intent alerts for watched corridors/buyers
06:00  REPORT     → write KPIs (new buyers, corroboration, freshness, calibration) to admin dashboard
```

## §7.2 Orchestrator requirements
| Requirement | Design |
|-------------|--------|
| Discover new companies | Delta watchers per connector |
| Refresh existing | Due-based scheduler (per-source cadence) |
| Merge duplicates | Resolution stage, reversible, audited |
| Update Trust Scores | Nightly recompute + decay |
| Remove invalid | Lifecycle: dormant→dissolved→archive; hard-delete only for erasure |
| Validate websites | HTTP liveness + MX check |
| Validate emails | ZeroBounce/NeverBounce credits |
| Check sanctions | Daily re-screen (hard gate) |
| Refresh govt records | Registry APIs/streams (event-driven where available) |
| Generate AI summaries | Brain, grounded + citation-bound |

## §7.3 Operational guardrails
- **Idempotent + incremental** (only changed data); safe to re-run.
- **Provenance-appending** (never destructive overwrite).
- **Rate-limit aware** per source; backoff on 429/403.
- **Failure isolation:** one connector failing doesn't halt the DAG; failed stages retried + alerted.
- **Cost guard:** cap paid verifications/LLM calls per night; prioritize high-value corridors.
- **Observability:** every stage writes metrics + errors to admin dashboard.
