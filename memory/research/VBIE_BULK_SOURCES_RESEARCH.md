# VBIE Deep Research — Official Bulk Data Sources (Global Buyer Intelligence)
**Prepared as: CTO-grade research deliverable • Research-first phase (NO production code written)**
**Date:** June 2026
**Scope:** Legal + Technical + Commercial + Architectural assessment of every official, legal, commercially-reusable, bulk-downloadable company / importer / exporter dataset that can become the foundation of LeadNation VBIE.

> ⚠️ **Disclaimer:** This is an operational/compliance assessment grounded in the actual licence texts of each source (cited). It is **not formal legal advice**. Before monetizing bulk reuse at scale, a qualified lawyer should give final sign-off per source, especially for GDPR/personal-data and any "yellow" source.

---

## 0. The single most important strategic insight (read first)

There are **two fundamentally different data types**, and LeadNation needs both but must not confuse them:

| Type | What it tells you | Examples | Buyer value |
|---|---|---|---|
| **A. Buying SIGNAL** (who is actively buying/importing) | Demand evidence — real procurement / import activity | EU TED, Canada CID (importers by HS), US Census trade | 🟢 **HIGH** — this is the actual "buyer" |
| **B. Company IDENTITY** (who exists, legally) | Registry identity, address, status, SIC/NAICS | Companies House, SIRENE, ACRA, ABN, LEI | 🟡 **MEDIUM** — enrichment + dedupe, NOT a buyer by itself |

**A company registry is NOT a buyer list.** Companies House tells you 5M UK companies *exist*; it does not tell you which are *importing pumps from India this quarter*. The VBIE moat = **fusing SIGNAL (A) with IDENTITY (B)** so every surfaced buyer has (1) real buying evidence and (2) a verified legal identity + GEID.

**GLEIF LEI (CC0, public domain) is the global identity backbone** that lets us dedupe and link A↔B across all countries. This is the "goldmine you didn't know you needed."

---

## PART 1 — 🇨🇦 Canada Deep Research (Highest Priority)

### 1.1 What is the official dataset?
- **Primary (SIGNAL):** **Canadian Importers Database (CID)** — ISED (Innovation, Science and Economic Development Canada). Lists **companies importing goods into Canada**, by HS code, product, city, and country of origin.
  - Portal: `open.canada.ca/data/en/dataset/2e7c5a58-986f-402c-9dec-a45e0dadf8dd`
  - Browse UI: `ised-isde.canada.ca/app/ixb/cid-bdic/`
- **No official exporter database** with named companies (Canada publishes importer lists, not exporter lists, as open data).
- **Company IDENTITY:** Corporations Canada (federal registry) exists but provincial registries are fragmented; CID is the high-value piece.
- **Trade context:** "Trade Data Online" (aggregate stats, not named companies).

### 1.2 Legal Review — CID
- **Licence:** **Open Government Licence – Canada 2.0 (OGL-Canada-2.0)**.
- **Exact clause (commercial use):** the licence grants a *"worldwide, royalty-free, perpetual, non-exclusive licence to use the Information, including for commercial purposes"* — copy, modify, publish, translate, adapt, distribute.
- **Condition:** attribution — *"Contains information licensed under the Open Government Licence – Canada."* + link to licence where possible.
- **Exclusions:** does **not** license personal information, third-party rights, or official symbols; must not imply endorsement.

| Question | Answer |
|---|---|
| Commercial use | ✅ Yes (explicit) |
| Attribution | ✅ Required |
| Redistribution | ✅ Yes |
| Resale | ✅ Yes (within licence, must not imply endorsement) |
| Monetization | ✅ Yes |
| Store in MongoDB | ✅ Yes |
| Searchable in LeadNation | ✅ Yes |
| Subscriber-only access | ✅ Yes (we can gate our value-add) |
| Modification / enrichment | ✅ Yes |
| AI processing | ✅ Yes |

**Legal risk rating: 🟢 GREEN.** (CID is aggregated importer lists, so personal-data risk is low — these are company names, not individuals.)

### 1.3 Bulk Download
- **Formats available:** ✅ **CSV** (multiple files: Major Importers by product / country / city / HS code; HS6 & HS10 description files). ❌ no JSON/XML/API for the bulk product.
- **Snapshot cadence:** annual/periodic release (e.g., "Canadian Importers Database 2022"). **Not** daily/monthly incremental.
- ⚠️ **Known gotcha (from our own logs + docs):** direct hot-link CSV fetch returned empty/zero-byte from our pod host previously. **Fix:** download from the `open.canada.ca` dataset resource URLs (not the ISED app hot-link), follow redirects, set a real User-Agent, and store the file to disk first (don't stream-parse a possibly-empty body). Validate `len(text) > 0` before parsing (our connector already guards this).
- **Best method:** ⭐ **Bulk CSV download** from the Open Canada dataset resource, staged to a raw-archive bucket, then parsed offline.

### 1.4 Technical Integration (design only)
- **Canada Connector:** fetch each CID resource CSV → stage raw → parse rows (Company, HS6/HS10, origin country, city).
- **Bulk Import Pipeline:** raw archive → normalize → dedupe (by normalized name + city) → LEI match → GEID → upsert into `entities` (`entity_type='buyer'`, `role='importer'`).
- **Incremental updates:** annual snapshot → diff against last snapshot → mark new/removed; version the provenance.
- **Duplicate detection:** normalized-name + city key; then GLEIF LEI fuzzy match to collapse cross-source dupes.
- **Trust Score:** SIGNAL source (real import activity) → higher base trust than pure-registry identity. Add "government open data" + "buying evidence" factors.
- **Evidence Panel:** "Imports [product] (HS xxxx) from [origin] — source: Canadian Importers Database (ISED), OGL-Canada 2.0" + link.
- **Country/GEID mapping:** country = CA; GEID = deterministic hash of natural key (already implemented pattern `cid:CA:<norm-name>`).
- **Brain integration:** answerable as "Who imports [product] into Canada?" with cited evidence + subscription gate.
- **App integration:** consumed via shared `/api/buyers/*` — no separate copy.

### 1.5 Compare: Canada API vs Canada Bulk
- There is **no official Canada CID API** — only the bulk CSV product. ⭐ **Recommendation: Bulk CSV.** (Provincial registry APIs exist but are out of scope for buyer signal.)

---

## PART 2 — 🇬🇧 UK Companies House: Bulk vs API

| Factor | REST API | Bulk "Free Company Data Product" (monthly CSV) |
|---|---|---|
| Coverage | Targeted queries (advanced-search by SIC) | **Full snapshot of ~5M active companies** |
| Freshness | Real-time per record | Monthly snapshot (updated within 5 working days of month-end) + daily update files |
| Rate limits | **600 requests / 5 min** (hard; ban risk if bypassed) | None — single file download |
| Storage cost | Low (only what you pull) | Higher (full register), but trivial for Mongo at this scale |
| Mongo indexing | Incremental | One-time bulk load + monthly re-diff |
| Update speed | Slow for millions (rate-limited) | Fast (one file) |
| Best for | Freshness on specific companies | **Building & maintaining the base corpus** |

- **Licence:** Open Government Licence v3.0 — commercial reuse explicitly allowed, incl. *"combine it with other Information... include it in your own product or application"*; **attribution required.**
- 🚫 **Hard boundary:** director / PSC data = personal data under UK GDPR → **never** use individuals' personal details for marketing/contact.

⭐ **Recommended architecture:** **Hybrid — Bulk primary + API for freshness.**
1. Monthly **bulk CSV** load builds/refreshes the base identity corpus (no rate-limit pain).
2. **REST API** used sparingly (within 600/5min) for on-demand freshness when a subscriber opens a specific company or for the importer/wholesaler SIC subset we surface as buyers.

---

## PART 3 — Country-by-Country Report

**Legend:** 🟢 Green = open, commercial reuse OK, bulk available · 🟡 Yellow = usable with conditions/limits · 🔴 Red = not reusable / paid-licence / prohibited.
**Type:** SIGNAL (buying activity) vs IDENTITY (registry).

| # | Country | Official source | Type | Bulk? | API? | Commercial reuse | Licence | Risk | Buyer value | Priority |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 🇪🇺 **EU-wide** | **TED** (Tenders Electronic Daily) | SIGNAL | ✅ CSV/bulk | ✅ | ✅ Free reuse | metadata CC0 / editorial CC BY 4.0 | 🟢 | ⭐ HIGH (public buyers) | **P0 (live)** |
| 2 | 🌐 **Global** | **GLEIF LEI** (Level 1 + 2) | IDENTITY | ✅ concatenated files | ✅ | ✅ | **CC0** (public domain) | 🟢 | Backbone (dedupe/GEID) | **P0** |
| 3 | 🇨🇦 Canada | **Canadian Importers DB** | SIGNAL | ✅ CSV | ❌ | ✅ | OGL-Canada 2.0 | 🟢 | ⭐ HIGH (real importers) | **P0** |
| 4 | 🇬🇧 UK | **Companies House** (bulk + API) | IDENTITY | ✅ CSV | ✅ | ✅ | OGL v3.0 | 🟢 (PSC=GDPR) | MED-HIGH | **P0 (key ready)** |
| 5 | 🇫🇷 France | **INSEE SIRENE** | IDENTITY | ✅ full stock + daily | ✅ | ✅ | Etalab Open Licence 2.0 | 🟢 | MED-HIGH (~10M estab.) | **P1** |
| 6 | 🇳🇴 Norway | **Brønnøysund Enhetsregisteret** | IDENTITY | ✅ full dataset | ✅ free | ✅ | NLOD | 🟢 | MED | P1 |
| 7 | 🇫🇮 Finland | **PRH / YTJ** | IDENTITY | ✅ file + API | ✅ | ✅ | CC BY 4.0 (no emails/phones) | 🟢 | MED | P1 |
| 8 | 🇩🇰 Denmark | **CVR / virk.dk** | IDENTITY | ✅ | ✅ | ✅ (m2m may need reg.) | Open (Danish gov) | 🟢 | MED | P1 |
| 9 | 🇨🇿 Czechia | **ARES** | IDENTITY | ✅ CSV/open data | ✅ | ✅ | Open data | 🟢 | MED | P1 |
| 10 | 🇦🇺 Australia | **ABN Bulk Extract** | IDENTITY | ✅ | ✅ (ABN Lookup) | ✅ (public subset) | CC BY 3.0 AU | 🟢 (no marketing implied) | MED | P1 |
| 11 | 🇸🇬 Singapore | **ACRA (data.gov.sg)** | IDENTITY | ✅ | ✅ | ✅ "free forever personal/commercial" | Open Data Licence (Singapore) | 🟢 | MED | P1 |
| 12 | 🇯🇵 Japan | **NTA Corporate Number** (+gBizINFO) | IDENTITY | ✅ full + daily change | ✅ Web API | ✅ | CC BY 4.0 (per secondary) | 🟢 | MED | P1 |
| 13 | 🇺🇸 USA | **SEC EDGAR** (public cos.) | IDENTITY | ✅ nightly ZIP | ✅ | ✅ free | US Gov public domain | 🟢 | LOW-MED (securities filers only) | P2 |
| 14 | 🇺🇸 USA | **SAM.gov** entity (public API/extract) | IDENTITY | ✅ extract API (1M rec) | ✅ | 🟡 only non-D&B public fields | ToU (D&B carve-out) | 🟡 | LOW-MED | P2 |
| 15 | 🇺🇸 USA | **Census trade** (USA Trade Online / Intl Trade API) | SIGNAL (aggregate) | partial | ✅ (Intl Trade API free; UTO paid) | context only | US Gov | 🟡 | context, NOT named buyers | P2 |
| 16 | 🇺🇸 USA | **State SOS registries** | IDENTITY | varies by state | varies | varies (some open, some paid) | per-state | 🟡 | MED (fragmented) | P3 |
| 17 | 🇳🇱 Netherlands | **KVK open dataset** | IDENTITY | ✅ basic dataset | ✅ | ✅ basic only | CC BY 4.0 (paid extracts separate) | 🟡 | MED | P2 |
| 18 | 🇪🇸 Spain | **BORME** (gazette) | IDENTITY (events) | ✅ datasets/feeds | ✅ (3rd-party) | ✅ BORME open; full register restricted | open data + attribution | 🟡 | LOW-MED | P2 |
| 19 | 🇵🇱 Poland | **KRS + CEIDG** (official APIs) | IDENTITY | via API | ✅ | ✅ (GDPR limits) | open API / public data | 🟡 (GDPR) | MED | P2 |
| 20 | 🇸🇪 Sweden | **Bolagsverket** | IDENTITY | mixed | ✅ | 🟡 product-dependent | no single clean open licence | 🟡 | MED | P2 |
| 21 | 🇰🇷 South Korea | Public Data Portal / DART | IDENTITY/filings | unclear | partial | 🟡 (policy allows unless restricted) | unclear bulk | 🟡 | MED | P3 |
| 22 | 🇧🇷 Brazil | **Receita Federal CNPJ** | IDENTITY | ✅ monthly CSV | ❌ official (3rd-party exist) | 🟡 likely, per terms + LGPD | Dados Abertos + LGPD | 🟡 (LGPD; sole-prop = personal) | MED | P2 |
| 23 | 🇴🇲 Oman | **Open Data Portal** | mixed | some datasets | some | ✅ "any commercial purpose" + attribution | Oman Open Data policy | 🟡 (coverage limited) | LOW-MED | P3 |
| 24 | 🇦🇪 UAE | Dubai Pulse DED / emirate portals | IDENTITY | ✅ some (DED CSV, weekly) | some | 🟡 per-dataset terms | fragmented (federal/emirate/free-zone) | 🟡 | MED | P3 |
| 25 | 🇩🇪 Germany | **OffeneRegister.de** (Handelsregister mirror) | IDENTITY | ✅ | partial | 🟡 CC BY 4.0 + OpenCorporates DB rights + naming restriction | CC BY 4.0 (with caveats) | 🟡 | MED-HIGH (large economy) | P2 |
| 26 | 🇮🇹 Italy | **Registro Imprese** (InfoCamere) | IDENTITY | ❌ (paid) | ✅ (paid) | 🔴 not open; paid commercial channel | proprietary/paid | 🔴 | — | P3 (paid only) |
| 27 | 🇧🇪 Belgium | **CBE / KBO** | IDENTITY | ✅ (after reg.) | ✅ | 🔴 commercial reuse = **€30,000/yr** | non-comm free / comm paid | 🔴 | — | ❌ reject (unless paid) |
| 28 | 🌐 **UN Comtrade** | Trade statistics | SIGNAL (aggregate) | ✅ (subscriber) | ✅ | 🔴 redistribution needs licence (UN copyright) | UN copyright | 🔴 for redistribution | context only | P3 (internal context) |
| 29 | 🇶🇦 Qatar | MCI / QFC public register | IDENTITY | ❌ | search only | 🔴 not established | service-based | 🔴 | — | reject for now |
| 30 | 🇿🇦 South Africa | **CIPC** | IDENTITY | ❌ open bulk | ✅ (controlled) | 🔴 restricted / service licence | CIPC terms | 🔴 | — | reject for now |
| 31 | 🇸🇦 Saudi Arabia | MC / Wathq APIs | IDENTITY | ❌ | ✅ (terms apply) | 🟡 source-specific, no free bulk | per-service | 🟡/🔴 | LOW | P3 |
| 32 | 🇲🇽 Mexico | — | — | ❓ unverified | ❓ | ❓ | — | ⚪ unknown | — | research later |
| 33 | 🇹🇷 Turkey | — | — | ❓ unverified | ❓ | ❓ | — | ⚪ unknown | — | research later |
| 34 | 🇻🇳 Vietnam | — | — | ❓ unverified | ❓ | ❓ | — | ⚪ unknown | — | research later |
| 35 | 🇹🇭 Thailand | DBD | IDENTITY | ❓ unverified | some | ❓ | — | ⚪ unknown | — | research later |

> **Rejections (do not ingest for commercial bulk):** 🔴 Belgium CBE (€30k/yr for commercial), 🔴 Italy Registro Imprese (paid/proprietary), 🔴 UN Comtrade redistribution (UN copyright — internal/context use only, never republish rows as our own dataset), 🔴 South Africa CIPC & Qatar (restricted/service-based). 🟡 SAM.gov D&B fields (exclude `evsSource=D&B`/`dnbOpenData=Y`; keep only post-4/4/2022 US-Gov public fields).

---

## PART 4 — Bulk Data Strategy (scaling to millions)

**Which combination scales best:**

1. ⭐ **Official Bulk Data Products = the backbone (80%).** Single monthly file per country → cheap, fast, no rate-limit risk, terms-clean. (CH, SIRENE, ABN, ACRA, Japan NTA, GLEIF, Czech ARES, Nordics.)
2. **REST APIs = freshness layer (15%).** On-demand per-record refresh when a subscriber opens a profile; nightly delta pulls for high-value SIC/NAICS subsets. Respect each source's rate limit (CH 600/5min; SAM 1,000/day).
3. **Daily/incremental update files = maintenance.** SIRENE daily, NTA daily-change, CH daily updates → apply diffs, don't re-ingest full snapshots.
4. **RSS / official feeds (Spain BORME gazette) = event stream** for company changes.
5. **Streaming APIs:** none of the official sources offer true streaming; not needed.

**Why bulk wins:** at millions of records, per-record API calls are rate-limited into the ground. Bulk file → stage → parse offline → bulk-write to Mongo (we already learned: **use `bulk_write` in chunks of 500, never per-doc Atlas round-trips**).

---

## PART 5 — Database Architecture (the pipeline)

```
                ┌──────────────────────────────────────────────────────┐
                │  0. SOURCE REGISTRY (mongo: vbie_sources)             │
                │  status: pending_legal_approval | active              │
                │  licence, attribution, terms_version, retrieved_at    │
                └──────────────────────────────────────────────────────┘
                                     │ (only 'active' sources run)
   BULK FILES / APIs                 ▼
   (CH, SIRENE, CID, LEI...) ──►  1. RAW ARCHIVE  (object storage / GridFS)
                                   • immutable original file per snapshot
                                   • proves provenance & terms compliance
                                     │
                                     ▼
                                  2. NORMALIZED / STAGING LAYER (mongo: vbie_staging)
                                   • one schema: name, country, address, ids,
                                     sic/naics, source_id, evidence, licence
                                   • sanctions screen (CSL) here (hard gate)
                                     │
                                     ▼
                                  3. VBIE ENTITY GRAPH (mongo: entities)  ← SINGLE SOURCE OF TRUTH
                                   • GEID (deterministic) = canonical identity
                                   • LEI-linked dedupe/merge
                                   • trust, confidence, freshness, provenance[]
                                   • admin_edited / admin_deleted sovereignty
                                     │
                                     ▼
                                  4. BRAIN CACHE (mongo: brain_cache / vbie_market_stats)
                                   • pre-computed answers, corridor stats,
                                     nightly re-scored aggregates
                                     │
                     ┌───────────────┴────────────────┐
                     ▼                                 ▼
              Website (VBIE API)                Mobile App (same VBIE API)
              /api/buyers/*                     /api/buyers/*   ← NO duplicate store
```

**Rules:**
- **One MongoDB, one `entities` graph, one GEID, one Brain.** Website backend is the **single writer** of the buyer graph (matches existing `vbie_connectors.py` single-writer rule). DO/App never write buyers.
- Raw archive is **kept** (audit/compliance/re-processing) but never served to users.
- Staging is disposable/re-buildable; the entity graph is the durable truth.

---

## PART 6 — Brain Integration (scoring millions without reprocessing)

- **Merge duplicates:** deterministic **GEID** (hash of natural key) for idempotency + **GLEIF LEI** as the cross-source join key; fuzzy name+country+address for the rest. Merge = keep canonical, store `merged_into`.
- **Trust (v1):** weighted evidence — SIGNAL sources (import/procurement activity) > IDENTITY-only; +government/official source; +sanctions-clear; +registry-listed. (Extends current `compute_trust`.)
- **Confidence:** number & agreement of independent sources confirming the same entity (1 source = low, 3 corroborating = high).
- **Freshness:** `last_verified` vs source cadence; decays over time; refreshed on each snapshot/API touch.
- **Company-change detection:** diff each new snapshot vs previous → detect status change, address change, new import activity → emit signal + notification.
- **Version history:** append-only `provenance[]` + `history[]` entries (don't overwrite); store `terms_version` at ingestion.
- **Provenance:** every field cites (source_id, evidence_type, note, url, licence).
- **Nightly re-score WITHOUT reprocessing millions:** only re-score records **touched by today's deltas** (dirty-flagging) + a small rolling freshness-decay batch. Aggregate corridor stats are incrementally updated, not recomputed from scratch. This is the key to scale.

---

## PART 7 — Compliance Review (per capability)

✅ = permitted · 🟡 = permitted with condition · 🔴 = not permitted

| Source | download | store | enrich | merge | score | index | search | expose to subscribers | monetize | expose via API | expose to app |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **EU TED** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GLEIF LEI (CC0)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Canada CID (OGL)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **UK Companies House (OGL)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ — 🟡 **PSC/director personal data: no marketing/contact use** |
| **France SIRENE (Etalab)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (attribution: insee.fr + update date) |
| **Norway/Finland/Denmark/Czech** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (FI: no emails/phones) |
| **Australia ABN / Singapore ACRA / Japan NTA** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (AU: no implied marketing) |
| **SEC EDGAR** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **SAM.gov (non-D&B public)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ — 🔴 **exclude D&B fields; no scraping; no bulk resell of D&B** |
| **Germany OffeneRegister** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | 🟡 — attribute OpenCorporates; don't circulate as "Handelsregister" |
| **Netherlands KVK / Spain BORME / Poland KRS** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | 🟡 — basic/open fields only; GDPR for personal data |
| **Brazil CNPJ** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | 🟡 — LGPD; sole-proprietor rows are personal data |
| **UN Comtrade** | ✅ (subscriber) | ✅ internal | ✅ context | 🔴 | ✅ aggregate | 🟡 | 🟡 | 🟡 aggregate only | 🔴 | 🔴 | 🔴 — **never republish rows; context/aggregate only** |
| **Belgium CBE** | 🟡 | 🟡 | — | — | — | — | — | 🔴 | 🔴 | 🔴 | 🔴 — **commercial = €30k/yr; REJECT unless paid** |
| **Italy Registro Imprese** | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 — **paid/proprietary; REJECT for open bulk** |
| **South Africa CIPC / Qatar** | 🔴 | 🔴 | — | — | — | — | — | 🔴 | 🔴 | 🔴 | 🔴 — restricted/service-based; REJECT for now |

**Why the NOs:** Belgium & Italy explicitly price/withhold commercial bulk reuse; UN Comtrade is UN-copyrighted (redistribution needs a licence); SAM.gov D&B fields are contractually barred for "identifying prospective customers" (our exact use case); CIPC/Qatar are service-gated with no open bulk.

---

## PART 8 — Final CTO Recommendation

### 8.1 Ranking (weighted across Legal Safety, Data Quality, Buyer Value, Commercial Value, Scalability, Cost, Ease, 5-yr Strategic Value)

| Rank | Source | Why |
|---|---|---|
| 🥇 1 | **GLEIF LEI (CC0)** | Public domain, global, free, the identity backbone that makes every other source dedupe-able. Zero legal risk. |
| 🥇 2 | **EU TED** | Already live; real public buyers; free commercial reuse; the SIGNAL engine. |
| 🥇 3 | **Canada CID** | Real named importers (rare open SIGNAL), OGL-commercial, bulk CSV. Highest buyer value per legal-risk. |
| 🥈 4 | **UK Companies House** | Key ready; OGL; bulk+API; huge clean identity corpus. |
| 🥈 5 | **France SIRENE** | ~10M establishments, full open bulk, Etalab commercial. Massive EU identity coverage. |
| 🥉 6 | **ACRA (SG) / ABN (AU) / NTA (JP)** | Clean open licences, strategic APAC + India-corridor value. |
| 7 | **Nordics + Czech** | Small but pristine open data; easy wins. |
| 8 | **SEC EDGAR + SAM.gov (non-D&B)** | US identity, but partial coverage / D&B carve-out care. |
| 9 | **Germany OffeneRegister / NL KVK / Brazil CNPJ / Poland** | Big markets, but attribution/GDPR/LGPD/naming caveats. |
| ❌ | Belgium, Italy, UN Comtrade (redistribution), CIPC, Qatar | Rejected for open commercial bulk. |

### 8.2 The 5-year foundation of VBIE
**Build the moat on the GREEN SIGNAL + GREEN IDENTITY + CC0 backbone:**
- **Signal:** EU TED (live) + Canada CID → expand with US Census aggregate context.
- **Identity:** Companies House + SIRENE + ACRA + ABN + Japan NTA + Nordics/Czech.
- **Backbone:** GLEIF LEI (CC0) to unify everything under one GEID.
- **Screen:** trade.gov CSL sanctions on every record (already live).
- Everything ingested via **official bulk products** first, **APIs** for freshness, **no scraping**, per-source `status: pending_legal_approval` until you flip it on.

### 8.3 Five-Year Roadmap

| Phase | Timeline | Sources added | Outcome |
|---|---|---|---|
| **P0 (now → 3 mo)** | Foundation | GLEIF LEI backbone + Companies House (bulk+API) + Canada CID + keep TED/CSL | GEID dedupe live; UK+CA buyers; 1M+ identities |
| **P1 (3–9 mo)** | EU + APAC | SIRENE, Norway, Finland, Denmark, Czech, ACRA, ABN, Japan NTA | Multi-million entity graph; strong India-export corridors (EU/APAC) |
| **P2 (9–18 mo)** | Big markets w/ care | SEC EDGAR, SAM.gov (non-D&B), Germany OffeneRegister, NL KVK, Poland, Brazil CNPJ, Spain BORME | US + DE + BR + PL coverage; GDPR/LGPD guardrails |
| **P3 (18–36 mo)** | Frontier | Oman/UAE datasets, South Korea, Saudi (per-terms); research MX/TR/VN/TH | Gulf + emerging corridors |
| **P4 (3–5 yr)** | Intelligence layer | Change-detection, buyer timelines, matching/recommendation Brain, corridor forecasting | From "buyer directory" → "buyer intelligence platform" |

### 8.4 Non-negotiable guardrails (carry into every connector)
1. Per-source `status: pending_legal_approval` → **disabled until you explicitly activate.**
2. **Official bulk product > official API > (never) scraping.** Respect robots.txt / ToS / rate limits.
3. Capture **licence + terms_version + retrieved_at + attribution** on every record.
4. **No personal data for marketing/contact** (PSC/directors, sole-proprietors) — GDPR/LGPD.
5. **Exclude** SAM.gov D&B fields; **reject** Belgium/Italy/Comtrade-redistribution/CIPC/Qatar for open commercial bulk.
6. One Mongo, one GEID, one Brain — website is sole buyer-graph writer; app consumes the same API.
7. For any new external API integration → route through `integration_expert`, take keys via env only.

---

## Appendix A — Attribution strings to store per source
- **Canada CID:** "Contains information licensed under the Open Government Licence – Canada." + link
- **UK Companies House:** "Contains public sector information licensed under the Open Government Licence v3.0." + link
- **France SIRENE:** "Source: INSEE (www.insee.fr), Sirene, [last update date] — Licence Ouverte / Etalab 2.0"
- **GLEIF LEI:** CC0 — no attribution required (credit appreciated)
- **EU TED:** "Source: Tenders Electronic Daily (TED), © European Union" + link
- **Finland PRH/YTJ / Australia ABN / Japan NTA:** CC BY 4.0 / CC BY 3.0 AU — credit source + link
- **Germany OffeneRegister:** "Data: OffeneRegister.de / OpenCorporates, CC BY 4.0" (do NOT circulate as "Handelsregister")

## Appendix B — Known ingestion gotchas (from our history)
- Canada CID hot-link returns empty from pod → download from open.canada.ca resource, follow redirects, real UA, validate non-empty before parse.
- Always `bulk_write` in chunks (≤500), never per-doc Atlas writes.
- Long TED/bulk runs > 120s → run in background + status polling, never a blocking shell.
- Use `datetime.now(timezone.utc)`, never naive datetimes (analytics comparison bug).
- Placeholder/junk regex must use word boundaries (the "National/Nantes" false-positive incident).
