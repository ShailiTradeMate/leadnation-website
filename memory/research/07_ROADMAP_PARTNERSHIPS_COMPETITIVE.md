# Deliverables 10–14 — Roadmap · Quick Wins · Long-Term · Partnerships · Competitive Analysis

---

## Deliverable 14 — Competitive Analysis

| Competitor | Core asset | Coverage | Strengths | Structural weaknesses (LeadNation's opening) |
|------------|-----------|----------|-----------|----------------------------------------------|
| **ImportYeti** | US ocean BoL (free UI) | US-only | Free, simple, great SMB funnel | US-only; record-centric; no verification/trust; no global |
| **Panjiva (S&P Global)** | 2B+ shipment records | ~60 ctys | Enterprise depth, brand, analytics | Expensive; record-centric; weak entity resolution; not AEO/citable; no transparent trust |
| **ImportGenius** | US + LATAM BoL | ~25 ctys modular | Long history, US depth | Narrow; à-la-carte cost; contact decay; no trust layer |
| **Volza** | Mirror BoL + contacts | 70–200+ ctys | Breadth + contact data + lead-gen framing | Data freshness/accuracy questioned; India T2 truncation; unverified contacts; legal exposure on contacts |
| **Descartes Datamyne** | ~230 markets BoL | Global | Widest geographic breadth | Logistics-oriented; not buyer-verification; enterprise pricing |
| **Tendata / TradeInt / others** | BoL resale | Varies | Cheap access | Undifferentiated; same raw material |
| **ZoomInfo / Apollo (adjacent)** | B2B contacts | Global | Contact depth, intent | Not trade-specific; no shipment/customs truth; GDPR scrutiny |
| **ImportGenius/Panjiva + AI chat bolt-ons** | Chat over BoL | — | Trendy | Chat over stale rows ≠ trust; hallucination risk without provenance |

**The whitespace nobody owns:**
1. **Entity-resolved** buyers (not rows).
2. **Transparent Trust Score + provenance**.
3. **Multi-source fusion** (registries + procurement + stats + shipments + verified web).
4. **AEO/citable** buyer objects.
5. **Compliance-as-brand** (lawful-basis, opt-out honored).

LeadNation should position explicitly *against* "shipment-row resellers": **"They sell rows. We verify buyers."**

---

## Deliverable 11 — Quick Wins (0–90 days, low cost, high signal; mostly FREE sources)

1. **US Verified Importers (India→USA corridor):** ingest **US CBP ocean BoL** + resolve against **SAM.gov entity API** + company websites → ship a Tier-2/3 "Verified US Buyers" list. *All free.*
2. **Canada named-importer list:** load the **Canadian Importers Database (CID)** by HS code + verify via **Corporations Canada API** → instant verified importers nobody else surfaces cleanly.
3. **UK verified buyers:** **Companies House API** + HMRC trade stats + VIES → high-trust UK entities.
4. **Corridor sizing dashboards:** **UN Comtrade** + **ITC Trade Map** to show customers *where* demand is before selling buyers (great top-of-funnel + AEO content).
5. **Intent feed MVP:** **TED + SAM.gov + UNGM** tender ingestion → "live buying intent" alerts by HS/country.
6. **Sanctions screening bolt-on:** **trade.gov CSL** screening on every buyer surfaced today → immediate trust/differentiation.
7. **Trust Score v0 (rules-based):** ship the transparent factor breakdown even before ML resolution — the *explainability UX* is the wow.
8. **Programmatic AEO pages:** "Verified importers of {HS} in {country}" pages citing sources — feeds existing SEO/AEO engine and captures LLM citations. (Ties directly to the platform's existing P1 SEO backlog.)

---

## Deliverable 10 — Implementation Roadmap (phased)

### Phase 0 — Foundations (Month 0–1)
- Connector framework + provenance ledger + lawful-basis engine (design-for-compliance).
- Canonical schema + sanctions screening service.
- Pick flagship corridor: **India→USA**.

### Phase 1 — First Verified Corridor (Month 1–3) → *Quick Wins above*
- Ingest US CBP BoL + Comtrade + SAM.gov + Companies House (for UK) + CID (for CA).
- Entity resolution v1 (strong-key + fuzzy). Trust Score v0 (rules). Verification Tiers 0–3.
- Ship "Verified Buyers" object in LeadNation web/app for 1 corridor.

### Phase 2 — Trust & Intent (Month 3–6)
- Trust Score v1 (back-tested, decay, corroboration). Tier 4 "LeadNation Verified™".
- Intent alerts (TED/SAM/UNGM). Contact verification pipeline (lawful-basis gated).
- Expand to India→UAE + India→UK corridors.

### Phase 3 — Fusion Depth (Month 6–12)
- Add licensed shipment feed (Volza/ImportGenius tier) to fill non-transparent corridors.
- ML entity resolution; graph expansion (buyer→counterparty discovery).
- Trust & Provenance API (external, citable/AEO). Continuous new-buyer discovery engine.
- Partnerships live (EPC/chamber pilots).

### Phase 4 — Scale & Platform (Month 12–24)
- Roll out all 30 target countries by corridor priority.
- Trust-as-a-Service API + CRM integrations. Human-QA loop for Tier 4.
- Enterprise features (watchlists, team, audit) — dovetails with the existing "Trade Command Center Vol 2+" roadmap.

---

## Deliverable 12 — Long-Term Strategy (2–4 years)

1. **Become the trust standard:** "LeadNation Verified™" becomes the buyer-trust badge others cite — the "verified checkmark" of global trade.
2. **Trust-as-a-Service:** license the Trust Score + provenance API to CRMs, banks (KYB), trade finance, insurers, marketplaces.
3. **AEO dominance:** the citable buyer graph makes LeadNation the default source ChatGPT/Perplexity/Claude cite for "who imports X in country Y" — compounding organic + AI-search moat.
4. **Two-sided network:** let verified buyers *claim & confirm* their profiles (like Google Business) → self-reinforcing freshness + consent-based contact data (solves GDPR *and* accuracy at once).
5. **Trade-finance & risk adjacency:** Trust Score → creditworthiness/counterparty-risk products.
6. **Data cooperative:** anonymized, consented corridor insights sold as market intelligence.

---

## Deliverable 13 — Potential Partnerships

### Data providers (license, don't rebuild)
- **Volza / ImportGenius / Descartes Datamyne / Panjiva** — licensed shipment feeds for non-transparent corridors (buy commodity input; add value on top).
- **OpenCorporates** — registry gap-fill (esp. Germany/Italy/Spain where no free API).
- **handelsregister.ai / OpenRegister.de** — Germany registry API.
- **Email/phone verification** vendors (deliverability), **domain intelligence** vendors.

### Government & quasi-government (credibility + verified members)
- **India:** FIEO + EPCs (**APEDA, EEPC, CHEMEXCIL, Pharmexcil, GJEPC, CAPEXIL**) — verified exporter members; MoU potential.
- **Malaysia MATRADE, Thailand DITP, Sri Lanka EDB, Bangladesh EPB** — verified exporter directories.
- **US trade.gov / Commercial Service, UK DBT, Enterprise Singapore, Austrade** — market-access data + credibility.
- **GCC:** Saudi MoC (Wathq), UAE DED/free zones — official CR verification partnerships.
- **Chambers of Commerce** (national + bilateral, e.g. Indo-American, Indo-German) + **ICC**.
- **Multilaterals:** ITC (Trade Map), World Bank/WITS, UNGM — data + distribution.

### Ecosystem / distribution
- **Expo & trade-fair organizers** (exhibitor lists = fresh verified intent; already aligned with LeadNation's Expo module).
- **CRMs** (HubSpot/Salesforce/Zoho) — Trust API integrations.
- **Trade finance / KYB / insurance** players — Trust-as-a-Service buyers.

### Partnership priority (first 3)
1. **One Indian EPC** (e.g., FIEO or CHEMEXCIL) — verified members + credibility for flagship corridor.
2. **One licensed shipment feed** (Volza or ImportGenius) — corridor fill.
3. **One registry gap-fill** (OpenCorporates) — EU coverage without building.

---

## Closing note
Every recommendation here favors **free/open, high-trust, competitor-ignored sources first**, licensing only the commoditized shipment layer, and **investing LeadNation's build effort where the moat is: resolution, verification, trust, and provenance.** See `01_WHITEPAPER.md §9` for the consolidated final recommendation.
