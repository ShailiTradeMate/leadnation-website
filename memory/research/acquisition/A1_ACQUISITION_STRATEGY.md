# Deliverable 1 — Complete Buyer Acquisition Strategy

## §1. The acquisition philosophy
LeadNation must acquire buyers the way an intelligence agency acquires signals: **many independent sources, each weak alone, fused into a strong, evidenced identity.** No single source is trusted; corroboration creates trust.

Three acquisition motions run in parallel:
1. **Bulk backfill** — one-time ingestion of large open datasets (US CBP BoL, Canada CID, registries, Comtrade) to seed the graph.
2. **Nightly incremental** — autonomous daily discovery of *new* buyers and *changes* to existing ones.
3. **Event-driven capture** — real-time reaction to high-value signals (new tender, new shipment, expo, sanctions change).

## §2. The 9 acquisition channels (ranked by trust × cost efficiency)

| Rank | Channel | Trust | Cost | Named buyers? | Role |
|------|---------|:---:|:---:|:---:|------|
| 1 | **Government company registries** | ★★★★★ | Free/low | ✅ | Identity backbone (existence, standing) |
| 2 | **Public customs / Bill of Lading** (US ocean, LATAM, mirror) | ★★★★☆ | Free→licensed | ✅ | Proof of trade activity |
| 3 | **Government procurement / tenders** | ★★★★★ | Free | ✅ | *Intent* — buyers actively purchasing now |
| 4 | **Canada CID / named-importer open datasets** | ★★★★★ | Free | ✅ | Rare open importer lists |
| 5 | **Trade Promotion Orgs / Export Councils / Chambers** | ★★★★★ | Free/partner | ✅ | Verified members + partnership credibility |
| 6 | **Trade statistics (Comtrade/ITC/national)** | ★★★★★ | Free | ✗ (aggregate) | Corridor sizing + validation, not names |
| 7 | **Trade fairs / expo exhibitor lists** | ★★★★☆ | Free/partner | ✅ | Fresh intent + verification |
| 8 | **Company websites / trade news / RSS** | ★★★☆☆ | Free | ✅ | Reachability + enrichment + intent |
| 9 | **Licensed commercial datasets** (Volza etc.) | ★★★★☆ | Paid | ✅ | Fill non-transparent corridors |
| — | **LinkedIn / gated marketplaces** | ★★★☆☆ | High legal risk | ✅ | *Last resort*, official API/partner only |

## §3. The core insight: separate "discovery" from "verification"
- **Discovery** = finding a *candidate* buyer (cheap, noisy — any single source qualifies).
- **Verification** = proving it's real, active, reachable (expensive — requires corroboration).
Competitors conflate the two and sell noisy candidates as "buyers." LeadNation only *shows* verified entities, but *discovers* aggressively behind the scenes.

## §4. Corridor-first acquisition (not country-first)
Acquire along **trade corridors** (origin→destination + HS family), because a buyer only matters relative to what a LeadNation user sells. Flagship order:
1. India→USA · 2. India→UAE · 3. India→UK · 4. India→Canada · 5. India→SG/ASEAN.
Each corridor is "acquired" when we have ≥N Tier-3 verified buyers with evidence.

## §5. Intent-led vs. history-led acquisition
- **History-led** (BoL/customs): who *has* imported → lagging but concrete.
- **Intent-led** (tenders, expos, RFQs, facility expansion, hiring): who is *about to* buy → leading, higher conversion, and almost nobody fuses it.
Combine: a buyer with **both** shipment history *and* a live tender is the highest-value lead → top Trust ranking.

## §6. "No account required" growth (end-goal requirement)
The database must improve **without** users signing up:
- Nightly autonomous pipeline (§Pipeline in A5) is the primary engine.
- Public, AEO-optimized verified-buyer pages generate organic + LLM-citation traffic → traffic itself surfaces correction signals.
- Optional *buyer self-claim* (like Google Business Profile) adds consent-based freshness later — a bonus, not a dependency.

## §7. What "acquired" means — the deliverable object
Every acquired buyer is a **Verified Buyer Object**: canonical entity + attributes + per-attribute provenance + Trust Score + evidence trail + freshness timestamps. This is the atomic unit shipped to product, API, and AEO pages.

## §8. Acquisition KPIs
- New Tier-2+ buyers/night per corridor.
- Corroboration depth (avg independent sources/buyer).
- Contactability rate (verified reachable / surfaced).
- Freshness (median age of top signal).
- Cost per verified buyer (target: driven toward near-zero via free sources).
- Trust calibration (score vs. deliverability/conversion).

## §9. Strategy in one paragraph
Seed the graph with massive free/official data, run an autonomous nightly resolve-verify-score pipeline, license shipment feeds only to cover blind corridors, gate personal data behind lawful basis, attach evidence + Trust Score to every buyer, and expose it all as citable pages/APIs. Depth-first by corridor, trust-first by design, autonomous by architecture.
