# Deliverable 2 — Country-by-Country Research

**Legend for access:** 🟢 Open/Free · 🟡 Free w/ registration or limited · 🟠 Paid/Licensed · 🔴 Restricted/Confidential · ⚙️ Official API · 📦 Bulk download · 🕷️ Scrape-only (no API)

**Reality check that shapes everything below:** transaction-level customs/BoL data is **public by default in only a minority of countries** (notably US *ocean* imports, India via mirror data, and much of Latin America). Most of the EU, Japan, Korea, and GCC publish **aggregated** trade statistics only. Company *registries*, by contrast, are broadly available and authoritative — this is where LeadNation should over-invest.

---

## SOUTH ASIA

### India (flagship)
- **Company registry:** MCA21 (Ministry of Corporate Affairs) — company master data, directors (DIN). 🟡 (portal + paid docs).
- **Importer/Exporter registry:** IEC (Importer-Exporter Code) via **DGFT**; own-IEC status & summary lookups on DGFT/ICEGATE. 🟡 (own records only).
- **Trade statistics:** **TradeStat** (`tradestat.commerce.gov.in`) 🟢 and **Commerce Dashboard** (`dashboard.commerce.gov.in`) 🟢 — commodity/country aggregates, HS 2–8 digit, ~24 months for private users. **DGCI&S** sells detailed rows (~₹1/row) 🟠.
- **Transaction-level buyer/seller names:** **Restricted since 26 Nov 2016** (Notification 140/2016-Customs). Not free/public. Available only via paid vendors using **counterpart-country mirror data** (Volza etc.), and recent data may be **truncated (T2 format)**. 🔴/🟠
- **Procurement (intent):** **GeM** (`gem.gov.in`) — no official public API 🕷️; **CPPP/eProcure** tenders.
- **Trade promotion:** **FIEO**, commodity **Export Promotion Councils** (APEDA, EEPC, CHEMEXCIL, Pharmexcil, etc.) — member directories 🟢/🟡; strong **partnership** targets.
- **Takeaway:** Use mirror data for India *exporters seen in buyer countries*; use registries + EPC directories for verification; never rely on domestic customs rows.

### Bangladesh
- **Registry:** RJSC (Registrar of Joint Stock Companies) 🕷️/🟡.
- **Customs:** NBR/ASYCUDA; no public transaction API. Data via Volza mirror (13.6M export / 22.5M import records, updated 2025) 🟠.
- **Trade promotion:** EPB (Export Promotion Bureau). Partnership target for RMG/textiles.

### Sri Lanka
- **Registry:** ROC (Dept. of Registrar of Companies) 🕷️/🟡.
- **Customs:** **Sri Lanka Customs Online Trade Statistics Platform** 🟢 (aggregates); EDB (`srilankabusiness.com`) exporter directory 🟢. Volza mirror 🟠.

### Nepal
- **Registry:** OCR (Office of Company Registrar) 🕷️. **Trade:** Dept. of Customs statistics 🟡 (aggregates), TEPC exporter directory. Low commercial-vendor coverage → rely on mirror + regional statistics.

### Bhutan
- **Registry:** RSEBL / MoICE registrar 🕷️ (small economy). **Trade:** Dept. of Revenue & Customs stats (aggregates) 🟡. Minimal vendor coverage; treat as long-tail, statistics-only.

---

## NORTH AMERICA

### USA (flagship)
- **Ocean import BoL:** **PUBLIC** under FOIA via CBP AMS/ACE 🟢📦 — shipper/consignee names+addresses, BoL number, goods, vessel, ports. **Air/truck manifests are NOT public** 🔴. Consignees can **opt out** (19 CFR §103.31, 2-yr confidentiality). This is the single richest free buyer source in the world → foundational.
- **Official stats:** USITC **DataWeb** ⚙️🟢 (Form 7501 entry summaries, no BoL); Census USA Trade Online.
- **Company registry:** No federal registry; state-level (Delaware, CA, etc.) 🕷️/🟡. Federal contractors in **SAM.gov Entity API** ⚙️🟢 (UEI/CAGE).
- **Procurement:** **SAM.gov** opportunities + entity APIs ⚙️🟢 (api.data.gov key; 10 req/day public, 1,000 registered).
- **Trade promotion:** `trade.gov` developer APIs ⚙️🟢 (market intelligence, consolidated screening list).

### Canada
- **Company registry:** **Corporations Canada** (ISED) federal — ⚙️🟢 Federal Corporation API (status, address, directors), JSON endpoints. Provincial registries separate, no unified API.
- **Importer list:** **Canadian Importers Database (CID)** — 🟢📦 importers by HS code, city, country of origin (based on CBSA data). *Rare open, named-importer dataset — high value.*
- **Trade stats:** StatCan **CIMT** ⚙️🟢📦 (HS 6/8/10, by province/country); Web Data Service API.
- **Procurement:** CanadaBuys (tenders) 🟡.

### Mexico
- **Registry:** SAT / RFC; **RUG / SIGER** commercial registry 🕷️/🟡.
- **Customs:** Strong **public manifest tradition** (LATAM) → excellent commercial vendor coverage (Panjiva/ImportGenius/Datamyne) 🟠; some via mirror. **Data Mexico** (`datamexico.org`) aggregates 🟢.
- **Trade promotion:** (post-ProMéxico) SE / state bodies.

---

## EUROPE (imports largely confidential → registry-led strategy)

> **Structural fact:** Intra-EU and most extra-EU *import* manifests are **not public**. EU strategy must be **registry + statistics + procurement (TED) led**, NOT BoL-led. **BRIS** is an inter-registry exchange, *not* a public API.

### United Kingdom
- **Registry:** **Companies House API** ⚙️🟢 (real-time: companies, officers, filings, PSC/beneficial owners; streaming API; free key, 600 req/5min). Best-in-class open registry.
- **Trade stats:** HMRC UK Trade Info ⚙️🟢📦.
- **Procurement:** Contracts Finder / Find a Tender (post-Brexit TED equivalent) 🟡.

### Germany
- **Registry:** **Handelsregister** — **no official public REST API** 🕷️; via third parties (handelsregister.ai, OpenRegister.de) 🟠. Unternehmensregister bulk.
- **Stats:** Destatis (GENESIS API) ⚙️🟢. **Procurement:** national + TED.

### France
- **Registry:** **INSEE Sirene API** ⚙️🟢 (~25M enterprises, SIREN/SIRET, daily updates, history since 1973; free account). Plus RNE / data.gouv.fr open data 📦.
- **Stats:** INSEE / Douanes. **Procurement:** BOAMP + TED.

### Italy / Spain / Netherlands / Belgium / Switzerland
- **Italy:** Registro Imprese (InfoCamere) 🟠 (paid), VIES for VAT validation 🟢.
- **Spain:** Registro Mercantil 🟠; **Netherlands:** KVK API ⚙️🟡 (paid/registered, high quality); **Belgium:** KBO/BCE Crossroads Bank 🟢📦 (open data extract); **Switzerland:** Zefix ⚙️🟢 (central business name index).
- **All EU:** **VIES** VAT-number validation 🟢⚙️ (EU-wide, great cheap verification signal), **TED** procurement ⚙️🟢, aggregator **OpenCorporates** 🟠 (covers most).

---

## MIDDLE EAST (GCC) — statistics + national registries; imports mostly aggregated

### UAE
- **Registry:** **Fragmented** — no single national registry. Mainland via each emirate **DED** (Dubai `business.dubai.gov.ae`, Abu Dhabi ADDED) 🕷️/🟡; free zones (DMCC, JAFZA, **DIFC** public register, **ADGM** public search) 🟢/🟡; federal **National Economic Register** `ner.economy.ae` aggregates licenses 🟡.
- **Trade:** GCC-Stat + FCSC/Dubai Customs (HS 4-digit dissemination) 🟡. New GCC digital customs data-link (2026) is govt-only.

### Saudi Arabia
- **Registry:** **Wathq** (Ministry of Commerce) ⚙️🟡 official CR API (trade name, status, capital, owners) via CR National Number; MoC Open Data 🟢. Third-party KYB (Lean, Signzy) 🟠.
- **Trade:** GASTAT + GCC-Stat aggregates 🟡.

### Qatar / Oman / Kuwait
- **Registries:** MoCI (Qatar), MoCIIP (Oman — "Invest Easy"), MoCI (Kuwait) 🟡/🕷️.
- **Trade:** national statistics authorities + **GCC-Stat** (`dp.gccstat.org`) 🟢/🟡 aggregates (HS 8-digit for most GCC).

---

## EAST & SOUTHEAST ASIA + OCEANIA

### Singapore
- **Registry:** **ACRA** — ⚙️🟡 API Marketplace (Entity Information Query launched Nov 2025); free **open datasets on data.gov.sg** (1.5M+ records, monthly) 🟢📦; live BizFile+ APIs restricted to approved partners.
- **Trade:** SingStat / Enterprise Singapore 🟢. Regional HQ hub → high-value corridor node.

### Malaysia
- **Registry:** **SSM** (paid e-Info) 🟠.
- **Trade:** **OpenDOSM** (`open.dosm.gov.my`) 🟢 + METS Online; MATRADE exporter directory 🟢 (partnership target).

### Vietnam
- **Registry:** National Business Registration Portal (dangkykinhdoanh) 🕷️/🟡.
- **Customs:** "Vietnam Customs Data" app (2025) is **govt-internal** 🔴; public shipment data via commercial vendors 🟠; GSO aggregates 🟢.

### Thailand
- **Registry:** DBD (Dept. of Business Development) DataWarehouse 🟡. **Trade:** Customs Dept + DITP (Thai Trade) exporter directory 🟢. Commercial mirror coverage decent 🟠.

### Indonesia
- **Registry:** AHU Online / OSS (NIB) 🕷️/🟡. **Trade:** BPS statistics 🟢; INATRADE. Mirror vendor coverage 🟠.

### Japan
- **Registry:** National Tax Agency **Corporate Number (Hōjin Bangō) API** ⚙️🟢 (free, all registered corporations); Houmukyoku registry (paid docs).
- **Customs stats:** **e-Stat** (`e-stat.go.jp`) ⚙️🟢📦 + Customs "Trade Statistics" downloads (CSV/DB API), monthly by commodity/customs/country. **Transaction-level named importers NOT public** 🔴 → registry + stats led.

### South Korea
- **Registry:** NTS Business Registration Number lookup 🟡; data.go.kr open APIs ⚙️🟢.
- **Customs:** KCS via **UNI-PASS** (declarations, not public dataset); **KITA** trade data is **membership-based** 🟠, no public customs API. → stats + registry + KITA partnership.

### Australia
- **Registry:** **ABN Lookup / ABR** — ⚙️🟢 free web service (GUID) + **weekly bulk XML on data.gov.au** 📦. ASIC company register (paid detail).
- **Trade:** **ABS** international merchandise trade ⚙️🟢 (via ausdata.io / ABS API), monthly by commodity. **Procurement:** AusTender 🕷️ (no official API).

### New Zealand
- **Registry:** **NZ Companies Register** (Companies Office) ⚙️🟢 (open, searchable, API-friendly); NZBN API ⚙️🟢 (business numbers). **Trade:** Stats NZ 🟢. One of the most open regimes globally.

---

## INTERNATIONAL / MULTILATERAL (cross-country backbone)

- **UN Comtrade** ⚙️🟡📦 — 200+ countries, HS-level, 1962→present; free registered tier (500 calls/day, 100k rows/call). Backbone for corridor sizing & sanity-checking. 🟢/🟡
- **World Bank WITS** 🟢 — Comtrade/TRAINS front-end.
- **ITC Trade Map / Market Access Map** 🟡 — 91 economies, 5,300 HS products; beta API on request; great for market selection.
- **WTO Stats** ⚙️🟢 — tariff/trade aggregates.
- **UNGM** ⚙️🟡 — UN procurement (OData v4: Notice/Award/VendorSanctions/LTA). Global intent + sanctions.
- **OpenCorporates** 🟠 — 140+ jurisdictions normalized registry aggregator (paid; fills registry gaps like Germany).
- **OFAC/EU/UN sanctions & consolidated screening (trade.gov CSL)** 🟢⚙️ — mandatory compliance filter.

---

## Corridor prioritization (where to win first)
| Rank | Corridor | Why | Best free sources |
|------|----------|-----|-------------------|
| 1 | **India → USA** | Huge, US ocean BoL public, high margin | CBP AMS BoL + Comtrade + SAM.gov |
| 2 | **India → UAE** | GCC re-export hub, diaspora demand | GCC-Stat + NER/DIFC/ADGM + Comtrade |
| 3 | **India → UK** | Companies House is best open registry | Companies House API + HMRC + Comtrade |
| 4 | India → Canada | CID names importers openly | CID + Corporations Canada + CIMT |
| 5 | India → Singapore/ASEAN | Hub distribution | ACRA data.gov.sg + OpenDOSM + Comtrade |
