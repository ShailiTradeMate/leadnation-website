# Deliverables 2, 3, 4, 5 — Source / API / Government / Commercial Matrices

Every source rated on the 10-point rubric. Fields legend (what's obtainable):
`Co`=Company name · `Web`=Website · `Em`=Email · `Ctry`=Country · `Prod`=Products · `HS`=HS code · `Imp`=Import history · `Exp`=Export history · `Cert`=Certifications · `Reg#`=Registration number · `Ph`=Phone · `Addr`=Address · `Ind`=Industry.
Access: 🟢 free · 🟡 free+reg/limited · 🟠 paid. API: ⚙️ yes · 📦 bulk · ❌ portal-only. Crawl: ✅/⚠️/⛔.

---

## Deliverable 4 — GOVERNMENT SOURCE MATRIX (highest trust; acquire first)

### 4A. Company / Business Registries (identity backbone)
| Source | Ctry | Official | Free | API | Download | Crawl | Fields | Refresh | Restrictions |
|--------|------|:---:|:---:|:---:|:---:|:---:|--------|--------|--------------|
| Companies House | UK | ✅ | 🟢 | ⚙️+stream | 📦 | n/a | Co,Reg#,Addr,Ind,directors,status | Real-time/daily | Personal (officers) = UK-GDPR |
| INSEE Sirene | FR | ✅ | 🟢 | ⚙️ | 📦 | n/a | Co,Reg#(SIREN/SIRET),Addr,Ind,status | Daily | GDPR on persons |
| Corporations Canada | CA | ✅ | 🟢 | ⚙️ | 📦(JSON) | n/a | Co,Reg#,Addr,directors,status | Weekly-monthly | PIPEDA |
| ACRA (data.gov.sg) | SG | ✅ | 🟡 | ⚙️/📦 | 📦 | n/a | Co,Reg#(UEN),Addr,Ind,status | Monthly (open); live=partner | PDPA |
| Wathq | SA | ✅ | 🟡 | ⚙️ | ❌ | n/a | Co,Reg#(CR),capital,owners,status | Real-time | Gov onboarding |
| gBizINFO (METI) | JP | ✅ | 🟢 | ⚙️ | 📦(CSV/JSON) | n/a | Co,Reg#(法人番号),Addr,Ind,Web,employees,**subsidies,contracts,certs,patents,financials** | Periodic | JP field names only; no phone/email |
| Corporate Number API (NTA) | JP | ✅ | 🟢 | ⚙️ | 📦 | n/a | Co,Reg#,Addr | Periodic | — |
| ABN Lookup / ABR | AU | ✅ | 🟢 | ⚙️ | 📦(weekly XML) | n/a | Co,Reg#(ABN),Addr,GST,status,Ind(ANZSIC gov-only) | Weekly | Some fields gov-only |
| NZBN / Companies Register | NZ | ✅ | 🟢 | ⚙️ | 📦 | n/a | Co,Reg#,Addr,directors,status | Real-time | — |
| Zefix | CH | ✅ | 🟢 | ⚙️ | partial | n/a | Co,Reg#,Addr,status | Daily | — |
| KBO/BCE | BE | ✅ | 🟢 | ⚙️ | 📦 | n/a | Co,Reg#,Addr,Ind,status | Daily | — |
| KVK | NL | ✅ | 🟡 | ⚙️ | limited | n/a | Co,Reg#,Addr,Ind | Daily | Paid per call |
| Handelsregister | DE | ✅ | 🟠 | ❌(3rd-party) | via vendor | ⚠️ | Co,Reg#,Addr,legal form,status | Event | No official API |
| Registro Imprese | IT | ✅ | 🟠 | ⚙️ | 📦 | n/a | Co,Reg#(P.IVA),Addr,Ind | Daily | Paid |
| Registro Mercantil | ES | ✅ | 🟠 | limited | ❌ | ⚠️ | Co,Reg#(NIF),Addr | Daily | Paid |
| MCA21 | IN | ✅ | 🟡 | ❌ | ❌ | ⚠️ | Co,Reg#(CIN),Addr,directors(DIN),status | Event | Paid docs; DPDP |
| SSM | MY | ✅ | 🟠 | ❌ | ❌ | ⚠️ | Co,Reg#,Addr,status | Event | Paid |
| DBD DataWarehouse | TH | ✅ | 🟡 | limited | ❌ | ⚠️ | Co,Reg#,Addr,financials | Event | — |
| AHU/OSS (NIB) | ID | ✅ | 🟡 | limited | ❌ | ⚠️ | Co,Reg#(NIB),Addr | Event | — |
| RJSC / ROC / OCR | BD/LK/NP | ✅ | 🟡 | ❌ | ❌ | ⚠️ | Co,Reg#,Addr,status | Event | Weak digital access |
| UAE DED + NER + DIFC/ADGM | AE | ✅ | 🟡 | partial | ❌ | ⚠️ | Co,License#,Addr,activity | Event | Fragmented by emirate/free-zone |
| VIES (VAT validation) | EU-27 | ✅ | 🟢 | ⚙️ | ❌ | n/a | Reg#(VAT)+name+Addr validation | Real-time | Validation only, not search |
| OpenCorporates (aggregator) | 140+ | ⚖️(aggregator) | 🟠 | ⚙️ | 📦 | n/a | Co,Reg#,Addr,directors,status | Varies | Paid; DB rights |

### 4B. Customs / Bill of Lading (proof of trade)
| Source | Ctry | Official | Free | API | Download | Named | Fields | Refresh | Restrictions |
|--------|------|:---:|:---:|:---:|:---:|:---:|--------|--------|--------------|
| CBP AMS/ACE ocean BoL (FOIA) | US | ✅ | 🟢/🟡 | ❌(FOIA/vendor) | 📦 | ✅ | Co(consignee/shipper),Addr,HS-ish,Prod,Imp,ports,vessel | Weekly | Air/truck confidential; consignee opt-out (19CFR103.31) |
| Canada CID | CA | ✅ | 🟢 | via TradeDataOnline | 📦 | ✅(importers) | Co,Addr(city/prov),HS,Prod,Ctry-of-origin | Annual (CBSA) | — |
| LATAM customs (MX/BR/CO/PE/EC) | LATAM | ✅ | 🟢/🟠 | mixed | 📦 | ✅ | Co,HS,Prod,Imp/Exp,volume | Monthly | Public-manifest tradition |
| Mirror data (via vendors) | 70–200 | ⚖️ | 🟠 | ⚙️ | 📦 | ✅ | Co(counterparty),HS,Prod,Imp/Exp,volume | Weekly | India T2 truncation; confidentiality varies |

### 4C. Trade statistics (aggregate — validation, not names)
| Source | Scope | Free | API | Fields | Refresh |
|--------|-------|:---:|:---:|--------|--------|
| UN Comtrade | Global | 🟡 | ⚙️📦 | Ctry,HS,Prod,Imp/Exp value/qty | Monthly |
| ITC Trade Map | 91 econ | 🟡 | ⚙️(beta) | Ctry,HS,trade indicators | Monthly |
| World Bank WITS / WTO | Global | 🟢 | ⚙️ | Ctry,HS,tariffs | Monthly/annual |
| USITC DataWeb / Census | US | 🟢 | ⚙️ | HS,Ctry,Imp/Exp | Monthly |
| StatCan CIMT | CA | 🟢 | ⚙️📦 | HS,Ctry,province,Imp/Exp | Monthly |
| Eurostat Comext | EU | 🟢 | ⚙️📦 | HS,Ctry,Imp/Exp | Monthly |
| HMRC UK Trade Info | UK | 🟢 | ⚙️📦 | HS,Ctry,Imp/Exp | Monthly |
| Japan e-Stat/Customs | JP | 🟢 | ⚙️📦 | HS,Ctry,Imp/Exp | Monthly |
| OpenDOSM | MY | 🟢 | 📦 | HS,Ctry,Imp/Exp | Monthly |
| ABS trade | AU | 🟢 | ⚙️ | HS,Ctry,Imp/Exp | Monthly |
| GCC-Stat | GCC | 🟡 | 📦 | HS(4–8),Ctry,Imp/Exp | Monthly/annual |

### 4D. Procurement / tenders (INTENT — buyers purchasing now)
| Source | Scope | Free | API | Fields | Refresh |
|--------|-------|:---:|:---:|--------|--------|
| TED | EU | 🟢 | ⚙️(REST+SPARQL) | Co(buyer/awardee),Addr,Prod,value,CPV | Daily |
| SAM.gov | US | 🟢 | ⚙️ | Co,Reg#(UEI/CAGE),Addr,opportunity,NAICS | Daily |
| UNGM | UN | 🟡 | ⚙️(OData) | Co,notice,award,sanctions | Daily |
| Contracts Finder / FTS | UK | 🟢 | ⚙️ | Co,value,CPV | Daily |
| CanadaBuys | CA | 🟡 | ⚙️ | Co,value | Daily |
| World Bank/ADB/AfDB tenders | Global | 🟢 | ⚙️/📦 | Co,project,award | Daily |
| GeM / CPPP | IN | 🟡 | ❌ | Co,dept,value | Daily (⚠️scrape) |
| AusTender | AU | 🟡 | ❌ | Co,value | Daily (⚠️scrape) |

### 4E. Trade Promotion Orgs / Councils / Chambers / Embassies (verified members)
| Source | Region | Free | API | Fields | Notes |
|--------|--------|:---:|:---:|--------|-------|
| FIEO + EPCs (APEDA/EEPC/CHEMEXCIL/Pharmexcil/GJEPC/CAPEXIL) | IN | 🟢/🟡 | ❌ | Co,Prod,Addr,Web,membership,Cert | Partnership targets; ⚠️ scrape dirs |
| MATRADE / DITP / EDB / EPB | MY/TH/LK/BD | 🟢 | ❌ | Co,Prod,Addr,Web | Verified exporters |
| trade.gov / DBT / Enterprise SG / Austrade | US/UK/SG/AU | 🟢 | ⚙️(trade.gov) | Co,market data,CSL | trade.gov CSL API ⚙️ |
| Embassy commercial sections / TFOs | Global | 🟢 | ❌ | Co,Prod,contacts | Relationship-driven |
| Chambers of Commerce (national/bilateral) + ICC | Global | 🟢/🟡 | ❌ | Co,Addr,membership | Partnership + verification |

---

## Deliverable 3 — API MATRIX (consolidated: has official API? auth? limits?)
| API | Auth | Free tier | Limit | Bulk | Priority |
|-----|------|:---:|-------|:---:|:---:|
| UN Comtrade | Free key | 🟡 | 500 calls/day, 100k rows | Premium | P0 |
| UK Companies House | Free key | 🟢 | 600/5min + stream | ✅ | P0 |
| INSEE Sirene | Free acct | 🟢 | generous | ✅ | P0 |
| Corporations Canada | Open | 🟢 | fair-use | JSON | P0 |
| Canada CID / TradeDataOnline | Open | 🟢 | fair-use | ✅ | P0 |
| gBizINFO | Free token | 🟢 | fair-use | ✅ | P1 |
| Japan Corporate Number | Free key | 🟢 | fair-use | ✅ | P1 |
| ABN Lookup | Free GUID | 🟢 | fair-use | weekly XML | P1 |
| ABS / e-Stat / Eurostat / HMRC / WITS | Open | 🟢 | fair-use | ✅ | P1 |
| ACRA Marketplace | Partner (live) / open datasets | 🟡 | per plan | ✅ | P1 |
| Wathq (SA) | Gov onboarding | 🟡 | per contract | ❌ | P2 |
| KVK / Zefix / KBO / NZBN | Open/registered | 🟢/🟡 | fair-use | mixed | P2 |
| VIES | Open | 🟢 | throttled | ❌ | P0 (verification) |
| TED | Anon/OAuth | 🟢 | fair-use | ✅ | P0 (intent) |
| SAM.gov | api.data.gov key | 🟢 | 10/day pub, 1000/day reg | ✅ | P0 |
| UNGM | Dev reg | 🟡 | per approval | partial | P1 |
| trade.gov (CSL/sanctions) | Free key | 🟢 | fair-use | ✅ | P0 (compliance) |
| OpenCorporates | Paid key | 🟠 | per plan | ✅ | P2 (gap-fill) |
| Volza / ImportGenius / Panjiva / Datamyne | License | 🟠 | per contract | ✅ | P1 (corridor fill) |
| Email verify (ZeroBounce/NeverBounce) | Key | 🟠 | per credit | ✅ | P1 (reachability) |

---

## Deliverable 5 — COMMERCIAL DATA PROVIDER MATRIX
| Provider | Coverage | 2026 entry price | Model | Named buyers | Contacts | Best use for LeadNation |
|----------|----------|------------------|-------|:---:|:---:|-------------------------|
| **Volza** | 70–209 ctys (mirror) | **~$1,500/yr** (Pro/Ent $5k–$25k+) | Tiered annual | ✅ | ✅ (decaying) | Broad emerging-market corridor fill; transparent price |
| **ImportGenius** | ~25 ctys (US+LATAM) | **~$1,794/yr** ($149–$399/mo) | Monthly+annual disc | ✅ | partial | US/LATAM depth |
| **Panjiva (S&P)** | ~60 ctys | **Custom** ($5k–$25k+, 3–30× Volza) | Enterprise | ✅ | ✅ | Enterprise depth + financials (later) |
| **Descartes Datamyne** | ~230 markets | **Custom** ($15k+) | Enterprise | partial | ✗ | Widest breadth (later, if needed) |
| **Tendata / TradeInt** | Varies | lower | Tiered | ✅ | partial | Cheap supplementary |
| **OpenCorporates** | 140+ registries | Paid API | Per-plan | ✅(entity) | ✗ | Registry gap-fill (DE/IT/ES) |
| **handelsregister.ai / OpenRegister** | DE | Per-call | API | ✅(entity) | ✗ | Germany registry |
| **ZoomInfo / Apollo** (adjacent) | Global contacts | High | Seat/credits | ✗(trade) | ✅ | Contact enrichment only (GDPR care) |
| **Email verify (ZeroBounce/NeverBounce)** | Global | $0.002–$0.02/email | Credits | n/a | verify | Deliverability gating |

**Buy recommendation:** start with **Volza** (transparent, broad, ~$1.5k) + registry gap-fill (**OpenCorporates**/handelsregister.ai) + **email verification credits**. Defer Panjiva/Datamyne to enterprise phase.
