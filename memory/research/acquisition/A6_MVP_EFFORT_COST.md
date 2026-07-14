# Deliverables 12, 13, 14, 15 — MVP + Effort + Cost + Final Recommendation

---

## Deliverable 12 — MVP RECOMMENDATION

### The MVP in one sentence
> **"1,000 Verified US Importers for the India→USA corridor, each with evidence + Trust Score, acquired 100% from free/official sources, refreshed nightly."**

### Why this MVP
- Uses only **free** sources → near-zero data cost, proves the model before spending on licenses.
- US ocean BoL is the world's richest free named-buyer source → fastest path to real verified buyers.
- Proves the *whole loop* (ingest → resolve → verify → score → attribute → refresh) on one corridor.
- Immediately demonstrable value: users see *verified, evidenced* buyers competitors can't match on trust.

### MVP scope (build)
| Component | MVP version |
|-----------|-------------|
| Connectors | US CBP ocean BoL (bulk/FOIA/vendor sample) · SAM.gov entity API · UK Companies House (for UK buyers) · Canada CID (for CA) · UN Comtrade (sizing) · trade.gov CSL (sanctions) · VIES (EU validation) |
| Normalize | Canonical schema + HS + name/address cleansing |
| Resolution | Strong-key (reg_id/domain) + fuzzy name/address (rules first) |
| Verification | Registry existence + trade proof + domain/MX + email verify + sanctions gate |
| Trust Score | v0 rules-based, transparent factor breakdown |
| Storage | `raw_records`, `entities`, `provenance`, `contacts`, `suppression` (per A4) |
| Serving | Discovery list + buyer detail w/ evidence trail; nightly refresh job |
| No-account | Public AEO buyer pages + nightly autonomy (no signup needed) |

### MVP explicitly EXCLUDES (defer)
- Paid licensed feeds (add in Phase 2 once model proven).
- ML matching (rules suffice for one clean corridor).
- LinkedIn/personal contact harvesting.
- Buyer self-claim portal, Trust-as-a-Service external API.

### MVP success criteria
- ≥1,000 Tier-2+ buyers, ≥60% with a verified contact channel, ≥95% resolution precision (sampled), nightly refresh runs unattended, every buyer renders an evidence trail.

---

## Deliverable 13 — ESTIMATED IMPLEMENTATION EFFORT

> Rough order-of-magnitude for a small senior team (indicative, not a commitment).

| Phase | Scope | Effort (person-weeks) | Team |
|-------|-------|----------------------|------|
| **MVP (Phase 1)** | 1 corridor, free sources, rules resolution, Trust v0 | **8–12 pw** (~2 devs × 5–6 wks) | 1 backend, 1 data eng, 0.5 legal review |
| Phase 2 — Trust & Intent | Trust v1 (decay/calibration), tenders (TED/SAM/UNGM), contact verify, +2 corridors | **10–14 pw** | +0.5 ML |
| Phase 3 — Fusion depth | Licensed feed integration, ML resolution, graph expansion, Trust API | **14–20 pw** | +1 ML/data |
| Phase 4 — Scale | 30 countries by corridor, QA loop, enterprise features | **ongoing** | data ops + eng |

**Effort drivers (hardest parts):** (1) entity resolution quality, (2) provenance + lawful-basis plumbing done right from day 1, (3) connector maintenance as sources change. Budget ~20% ongoing for connector upkeep.

---

## Deliverable 14 — COST ANALYSIS (grounded, 2026 figures)

### One-time / build
- Engineering (MVP): the 8–12 pw above (internal cost).

### Recurring data & infra (annual, indicative)
| Item | MVP (free-first) | Growth phase |
|------|------------------|--------------|
| Free gov/stats/procurement APIs (Comtrade, Companies House, SAM.gov, CID, gBizINFO, ABN, trade.gov, VIES...) | **$0** | $0 |
| US CBP ocean BoL | **$0–low** (FOIA / cheap vendor sample) | low |
| Licensed shipment feed — **Volza** | $0 (deferred) | **~$1,500/yr** entry (Pro/Ent $5k–$25k+) |
| ImportGenius (US/LATAM depth, optional) | — | ~$1,794/yr → ~$4,800 top tier |
| Panjiva / Datamyne (enterprise, later) | — | custom, ~$5k–$25k+/yr |
| Registry gap-fill (OpenCorporates / handelsregister.ai) | — | ~$1k–$5k/yr (per-plan) |
| Email verification (ZeroBounce/NeverBounce) | ~$0.008/email (NeverBounce entry) → ~$0.002 at 1M+ | e.g. 100k verifies ≈ **$500–$650** |
| Proxies (only if crawling public sites) | minimal | residential ~$5–$40/GB (avoid if API exists) |
| LLM (extraction/reconcile, Emergent key) | usage-based | scales with volume |
| MongoDB Atlas + search + compute | existing infra | scales with graph size |

### Cost narrative
- **MVP annual data cost ≈ under ~$1k** (mostly email verification), because identity + trade + intent come from **free** sources.
- **Growth to multi-corridor ≈ ~$3k–$10k/yr** (Volza + OpenCorporates + verification credits).
- **Enterprise breadth (Panjiva/Datamyne) only if a customer needs a non-transparent corridor** — pass cost through.
- **Cost per verified buyer trends toward near-zero** as free sources dominate — a structural margin advantage over volume resellers who pay for every row.

---

## Deliverable 15 — FINAL RECOMMENDATION

**Build the Verified Buyer Acquisition System as a free-source-first, autonomous, evidence-carrying pipeline — not a licensed-data reseller.**

Concretely, in priority order:
1. **Ship the MVP** (India→USA, 1,000 verified US importers, 100% free sources, Trust v0, evidence trail, nightly refresh). Prove the loop cheaply.
2. **Make the "Verified Buyer Object" the atomic product** — entity + Trust Score + provenance. Never surface unverified rows.
3. **Run the nightly orchestrator from day one** — this is what makes the DB "smarter every night" and satisfies "no account required."
4. **Gate personal data + screen sanctions from day one** — compliance-by-design is a moat, not overhead.
5. **License shipment data (Volza ~$1.5k) only to fill blind corridors** once the free-source model is proven.
6. **Expose evidence publicly (AEO pages) + later a Trust API** — turning trust into LeadNation's citable, defensible competitive advantage.
7. **Partner with 1 Export Promotion Council + 1 shipment vendor + 1 registry aggregator** to accelerate coverage and credibility.

**The defensible advantage:** competitors sell the same commoditized shipment rows. LeadNation sells **verified, evidenced, continuously-refreshed buyer identities** assembled mostly from free official sources at near-zero marginal cost — a product that is simultaneously *cheaper to run, more trustworthy, more legally durable, and more AI-citable* than anything on the market. That is how LeadNation becomes the world's most trusted Global Buyer Discovery Platform.

---

### Cross-references
- Country detail & source availability: `/app/memory/research/02_COUNTRY_RESEARCH.md`
- Full Trust Score + Verification Framework: `/app/memory/research/05_TRUST_AND_VERIFICATION.md`
- Architecture deep-dive: `/app/memory/research/06_ARCHITECTURE.md`
- Legal deep-dive: `/app/memory/research/04_LEGAL.md`
