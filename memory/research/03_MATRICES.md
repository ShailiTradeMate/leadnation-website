# Deliverables 3, 4, 5 — Data Source / API Availability / Crawler Feasibility Matrices

Three matrices below. Ratings are directional (June 2026 research) and must be re-confirmed under license before any production use.

**Cost:** 🟢 Free · 🟡 Free w/ registration or limited · 🟠 Paid/Licensed
**API:** ⚙️ Official API · 📦 Bulk/download · ❌ None (portal only)
**Crawl feasibility (if no API):** ✅ Feasible & low-risk · ⚠️ Feasible but ToS/legal risk · ⛔ Do not scrape (blocked/illegal/personal-data)
**Refresh:** how often the *source* materially changes

---

## Deliverable 3 — DATA SOURCE MATRIX (by category)

### A. Shipment / Bill of Lading (transaction-level)
| Source | Coverage | Cost | Named parties? | Notes |
|--------|----------|------|----------------|-------|
| US CBP AMS/ACE ocean BoL (FOIA) | US ocean imports | 🟢/🟡 | ✅ | Air/truck NOT public; consignee opt-out exists |
| Volza | 70–200+ ctys (mirror) | 🟠 | ✅ (decaying) | Best emerging-market breadth; India T2 truncation risk |
| Panjiva (S&P Global) | ~60 ctys | 🟠 | ✅ | Enterprise; strong Americas |
| ImportGenius | ~25 ctys modular | 🟠 | ✅ | US + LATAM depth, à la carte |
| Descartes Datamyne | ~230 markets | 🟠 | partial | ~85% global trade value; logistics focus |
| LATAM customs (MX, BR, CO, PE, EC) | LATAM | 🟢/🟠 | ✅ | Public-manifest tradition; cheap & rich |

### B. Company / Business Registries (identity core)
| Source | Country | Cost | Access | Crawl |
|--------|---------|------|--------|-------|
| Companies House | UK | 🟢 | ⚙️ + 📦 | n/a |
| INSEE Sirene | FR | 🟢 | ⚙️ + 📦 | n/a |
| Corporations Canada | CA | 🟢 | ⚙️ | n/a |
| ACRA (data.gov.sg + Marketplace) | SG | 🟡 | ⚙️/📦 | n/a |
| Wathq | SA | 🟡 | ⚙️ | n/a |
| Corporate Number API (NTA) | JP | 🟢 | ⚙️ | n/a |
| ABN Lookup / ABR | AU | 🟢 | ⚙️ + 📦 | n/a |
| NZBN / Companies Register | NZ | 🟢 | ⚙️ | n/a |
| Zefix | CH | 🟢 | ⚙️ | n/a |
| KBO/BCE | BE | 🟢 | 📦 | n/a |
| KVK | NL | 🟡 | ⚙️ | n/a |
| Handelsregister | DE | 🟠 | ❌ | ⚠️ (3rd-party APIs preferred) |
| Registro Imprese | IT | 🟠 | ⚙️ | n/a |
| SSM | MY | 🟠 | ❌ | ⚠️ |
| MCA21 | IN | 🟡 | ❌ | ⚠️ |
| OpenCorporates (aggregator) | 140+ | 🟠 | ⚙️ | n/a (fills gaps) |

### C. Trade statistics (aggregate — for sizing & validation, not names)
| Source | Scope | Cost | API |
|--------|-------|------|-----|
| UN Comtrade | Global | 🟡 | ⚙️📦 |
| World Bank WITS | Global | 🟢 | ⚙️ |
| ITC Trade Map | 91 econ | 🟡 | ⚙️(beta) |
| WTO Stats | Global | 🟢 | ⚙️ |
| USITC DataWeb / Census | US | 🟢 | ⚙️ |
| StatCan CIMT + CID | CA | 🟢 | ⚙️📦 (CID names importers!) |
| Eurostat Comext | EU | 🟢 | ⚙️📦 |
| HMRC UK Trade Info | UK | 🟢 | ⚙️📦 |
| Japan e-Stat / Customs | JP | 🟢 | ⚙️📦 |
| OpenDOSM | MY | 🟢 | 📦 |
| ABS trade | AU | 🟢 | ⚙️ |
| GCC-Stat | GCC | 🟡 | 📦 |

### D. Procurement / tenders (INTENT signals — underused goldmine)
| Source | Scope | Cost | API |
|--------|-------|------|-----|
| TED | EU | 🟢 | ⚙️ (REST + SPARQL) |
| SAM.gov | US | 🟢 | ⚙️ (opportunities + entity) |
| UNGM | UN global | 🟡 | ⚙️ (OData) |
| Contracts Finder / Find a Tender | UK | 🟢 | ⚙️ |
| CanadaBuys | CA | 🟡 | ⚙️ |
| GeM / CPPP | IN | 🟡 | ❌ (⚠️ scrape) |
| AusTender | AU | 🟡 | ❌ (⚠️ scrape) |
| World Bank / ADB / AfDB tenders | Global | 🟢 | ⚙️/📦 |

### E. Trade-promotion / membership directories (VERIFIED members — partnership upside)
FIEO & Indian EPCs (APEDA, EEPC, CHEMEXCIL, Pharmexcil, GJEPC…), MATRADE (MY), DITP/Thai Trade (TH), EDB (LK), EPB (BD), TFO/embassy commercial sections, national Chambers of Commerce, ICC. Mostly 🟢/🟡 directory pages; value = *verification + partnership*, not volume.

### F. Web / contact enrichment (reachability — highest legal sensitivity)
Company websites (🟢 ✅ crawl if robots-compliant), DNS/MX & domain age, LinkedIn company & people (⛔ personal data — official API/partner only), news/press (🟢), expo exhibitor lists (🟡/✅), job postings (intent).

### G. Sanctions / risk (mandatory filter)
OFAC SDN, EU consolidated list, UN Security Council, UK OFSI, **trade.gov Consolidated Screening List** ⚙️🟢, PEP lists. Always applied last.

---

## Deliverable 4 — API AVAILABILITY MATRIX (has official API? auth? limits?)

| Source | Official API | Auth | Rate/limits | Bulk |
|--------|:---:|------|-------------|:---:|
| UN Comtrade | ✅ | Free key | 100/hr guest; 500/day + 100k rows registered; 1–5 req/s | Premium only |
| UK Companies House | ✅ | Free key | 600 req / 5 min; streaming API | ✅ |
| INSEE Sirene | ✅ | Free account + subscribe | Generous free | ✅ |
| Corporations Canada | ✅ | Open | Fair-use | JSON |
| StatCan CIMT | ✅ (WDS) | Open | Fair-use | ✅ |
| Canada CID | via Trade Data Online | Open | portal + open dataset | ✅ |
| ACRA | ✅ (Marketplace) | Partner approval for live; open datasets free | varies | ✅ (data.gov.sg) |
| Wathq (SA) | ✅ | Gov onboarding | per contract | ❌ |
| Japan Corporate Number | ✅ | Free key | fair-use | ✅ |
| Japan e-Stat / Customs | ✅ | Free key | fair-use | ✅ |
| ABN Lookup (AU) | ✅ | Free GUID | fair-use | ✅ weekly XML |
| ABS trade (AU) | ✅ | Open | fair-use | ✅ |
| NZBN / NZ Companies | ✅ | Free/registered | fair-use | ✅ |
| Zefix (CH) | ✅ | Open | fair-use | partial |
| KVK (NL) | ✅ | Paid/registered | per plan | limited |
| VIES (EU VAT) | ✅ | Open (SOAP/REST) | throttled | ❌ |
| Eurostat Comext | ✅ | Open | fair-use | ✅ |
| HMRC UK Trade Info | ✅ | Open | fair-use | ✅ |
| TED (EU) | ✅ | Anon search / OAuth submit | fair-use | ✅ (SPARQL/OData) |
| SAM.gov | ✅ | api.data.gov key | 10/day public, 1,000/day registered | ✅ |
| UNGM | ✅ (OData) | Dev registration | per approval | partial |
| trade.gov (CSL etc.) | ✅ | Free key | fair-use | ✅ |
| OpenCorporates | ✅ | Paid key | per plan | ✅ |
| Handelsregister (DE) | ❌ official | 3rd-party keys | per vendor | via 3rd-party |
| GeM / AusTender / KITA | ❌ | — | — | scrape/partner |
| CBP AMS BoL (US) | ❌ realtime API | FOIA / vendor | — | ✅ (FOIA/CD/vendors) |
| Volza/Panjiva/ImportGenius/Datamyne | ✅ (paid tiers) | License | per contract | ✅ |

---

## Deliverable 5 — CRAWLER FEASIBILITY MATRIX (only where no clean API)

> Rule: **API/bulk/license first. Crawl only as last resort, robots-compliant, rate-limited, with legal sign-off, and NEVER for gated personal data.**

| Target | Feasible? | Risk | Recommendation |
|--------|:---:|------|----------------|
| Company public websites (contact/about) | ✅ | Low (respect robots.txt) | Crawl for domain/MX/company facts; avoid harvesting named personal emails without lawful basis |
| Expo/exhibitor & conference lists | ✅ | Low–med | High-value intent; prefer organizer data partnerships |
| Government portals w/o API (GeM, AusTender, some registries) | ⚠️ | Med (ToS varies) | Check ToS; many *permit* reuse of public data; prefer official open-data mirror |
| Handelsregister (DE) | ⚠️ | Med | Use licensed 3rd-party API (handelsregister.ai/OpenRegister), not raw scrape |
| SSM/MCA21 gated pages | ⛔ | High (auth/paywall) | License instead |
| LinkedIn profiles/people | ⛔ | High (GDPR + ToS; CNIL fined KASPR €240k) | Do NOT scrape; official API / opted-in / partner data only |
| Marketplaces (Alibaba/IndiaMART) behind auth | ⛔ | High (ToS) | Partnership or user-consented import only |
| Paid vendor sites (Volza pages etc.) | ⛔ | High | License the data; never scrape competitor output |
| News/press (RSS/sitemaps) | ✅ | Low | RSS + sitemaps preferred over scraping |

**Crawler engineering guardrails (if used):** respect `robots.txt` + crawl-delay; identify a real User-Agent; cache & de-dupe; per-domain rate caps; capture source URL + fetch timestamp for provenance; auto-stop on 403/429; legal review per new domain; quarantine any personal data into the lawful-basis pipeline (see `04_LEGAL.md`).
