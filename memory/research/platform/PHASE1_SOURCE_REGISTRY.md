# VBIE Phase 1 — 30-Country Source Registry for 10,000 Verified Buyers

> **Purpose:** Identify the concrete, legally-cleared sources across 30 countries from which LeadNation can assemble the **first 10,000 verified buyer records**.
> **Status:** Research/design artifact (Phase 1). **No production code.** Companion file: `sources_seed.json` (the master `sources` collection seed).
> **Gate discipline:** This is for your review & approval before Phase 2 (Architecture).

---

## §1. Critical definition — what is a "buyer detail"?
A buyer detail is **not** a company name. It is a **resolved entity with (a) verifiable identity + (b) evidence of trade/purchase intent**. So sources fall into two roles, and we need BOTH to make a "verified buyer":

- **Identity sources** (registries) → prove the entity *exists* (name, reg#, address, industry, status).
- **Buying-evidence sources** (customs/BoL, procurement awards, importer datasets, council membership) → prove the entity *actually buys/imports*.

A registry alone gives 30M companies but 0 verified *buyers*. Customs/procurement/importer data is what converts a company into a **buyer**. This is the filter that drives the 10K plan below.

## §2. The "buyer-yield" of each source class (why some sources matter more)
| Source class | Names buyers? | Buyer-yield | Notes |
|--------------|:---:|:---:|-------|
| **Public customs / Bill of Lading** (US ocean, LATAM) | ✅ named consignees | ★★★★★ | Richest free named-buyer source on earth |
| **Named-importer open datasets** (Canada CID) | ✅ importers by HS | ★★★★★ | Rare; directly = buyers |
| **Public procurement awards** (TED/SAM/UNGM/Contracts Finder) | ✅ named buyers + awardees | ★★★★☆ | Intent + confirmed purchasing bodies |
| **Licensed mirror BoL** (Volza/ImportGenius) | ✅ named counterparties | ★★★★☆ | Fills confidential-import corridors (EU/JP/GCC/AU) |
| **Company registries** | identity only | ★★★☆☆ | Backbone for verification, not discovery of "buyers" |
| **Trade councils / chambers / EPC directories** | ✅ verified members | ★★★☆☆ | Verified but skewed to *exporters*; partnership upside |
| **Trade statistics** (Comtrade/national) | ✗ aggregate | — | Sizing/validation only |
| **Company websites / news / RSS** | enrichment | ★★☆☆☆ | Reachability + intent signals |

**Takeaway:** the 10K comes primarily from **public customs (US) + named-importer datasets (CA) + procurement awards (US/EU/UK/JP/AU) + licensed mirror BoL (EU/JP/GCC/AU)**, with **registries as the verification backbone** everywhere.

---

## §3. THE 10,000-BUYER ACQUISITION PLAN (priority-10 countries)
Realistic first-wave allocation, weighted by free named-buyer availability. India is flagship-adjacent (mirror-only for domestic) and included in the registry, but the *first* 10K targets the user's priority-10.

| # | Country | Primary buyer-evidence source(s) | Identity/verify source | Free? | Target buyers |
|---|---------|----------------------------------|------------------------|:---:|:---:|
| 1 | 🇺🇸 USA | **CBP ocean BoL** (named consignees) + SAM.gov awardees | SAM.gov entity + state reg + website | ✅ | **4,000** |
| 2 | 🇨🇦 Canada | **Canadian Importers Database (CID)** by HS | Corporations Canada API | ✅ | **1,500** |
| 3 | 🇬🇧 UK | Contracts Finder/FTS awards + mirror BoL | **Companies House API** | ✅/🟠 | **800** |
| 4 | 🇯🇵 Japan | **gBizINFO gov-contract awardees** + mirror BoL | gBizINFO / Corporate Number | ✅/🟠 | **700** |
| 5 | 🇦🇺 Australia | **AusTender awardees** + mirror BoL | ABN Lookup bulk | ✅/🟠 | **600** |
| 6 | 🇩🇪 Germany | **TED awardees** + mirror BoL | Handelsregister (licensed) / VIES | 🟠 | **600** |
| 7 | 🇫🇷 France | **TED awardees** + mirror BoL | **INSEE Sirene API** | ✅/🟠 | **500** |
| 8 | 🇳🇱 Netherlands | **TED awardees** + mirror BoL | KVK API / VIES | ✅/🟠 | **500** |
| 9 | 🇸🇬 Singapore | mirror BoL + Enterprise SG intent | **ACRA open dataset** | ✅/🟠 | **400** |
| 10 | 🇦🇪 UAE | GCC mirror BoL + re-export data | NER / DIFC / ADGM registries | 🟠 | **400** |
| — | 🇮🇳 India (flagship) | mirror BoL (counterpart mfrs) + EPC member dirs | MCA21 / IEC | 🟠 | (separate corridor) |
|   | **TOTAL** | | | | **~10,000** |

**Cost to hit 10K:** free sources cover USA + Canada + registries + procurement (~6,000 buyers at ~$0 data cost). The remaining ~4,000 (EU/JP/AU/GCC confidential-import corridors) need **one licensed mirror feed (Volza ~$1,500/yr)**. Total first-wave data cost ≈ **under $2,000/yr**.

---

## §4. FULL 30-COUNTRY SOURCE REGISTRY
Columns: **Src**=source · **Role** (ID=identity / BUY=buying-evidence / STAT=aggregate / INTENT) · **Access** (🟢free/🟡reg/🟠paid) · **API** (⚙️/📦/❌) · **Names buyers?** · **Store** (P=permanent/C=cache/L=licensed/Live) · **Attrib** (attribution required) · **Personal?** · **Verdict** (✅allowed/⚠️restricted/⛔forbidden).

### PRIORITY 10

**🇺🇸 USA**
| Src | Role | Access | API | Names | Store | Attrib | Pers | Verdict |
|-----|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| CBP AMS/ACE ocean BoL (FOIA/vendor) | BUY | 🟢/🟡 | ❌(FOIA)/⚙️(vendor) | ✅ | P | rec | consignee names | ✅ (honor confidentiality opt-out; air/truck ⛔) |
| SAM.gov entity + opportunities | ID+INTENT | 🟢 | ⚙️ | ✅(awardees) | P | rec | — | ✅ |
| USITC DataWeb / Census | STAT | 🟢 | ⚙️ | ✗ | P | rec | — | ✅ |
| trade.gov CSL (sanctions) | RISK | 🟢 | ⚙️ | ✅(flag) | P | rec | names | ✅ (must use) |
| State business registries | ID | 🟡 | mixed | ✅ | P | — | officers | ⚠️ per-state |

**🇨🇦 Canada**
| Canadian Importers Database (CID) | BUY | 🟢 | 📦 | ✅ importers | P | rec | — | ✅ |
| Corporations Canada | ID | 🟢 | ⚙️ | ✅ | P | rec | directors | ✅ |
| StatCan CIMT | STAT | 🟢 | ⚙️📦 | ✗ | P | rec | — | ✅ |
| CanadaBuys | INTENT | 🟡 | ⚙️ | ✅ | P | rec | — | ✅ (CASL for outreach) |

**🇬🇧 UK**
| Companies House | ID | 🟢 | ⚙️+stream | ✅ | P | rec | PSC/officers | ✅ |
| Contracts Finder / Find a Tender | INTENT | 🟢 | ⚙️ | ✅ buyers+awardees | P | rec | — | ✅ |
| HMRC UK Trade Info | STAT | 🟢 | ⚙️📦 | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇯🇵 Japan**
| gBizINFO (METI) | ID+INTENT | 🟢 | ⚙️ | ✅(+gov contracts/subsidies) | P | rec | — | ✅ |
| Corporate Number API (NTA) | ID | 🟢 | ⚙️ | ✅ | P | rec | — | ✅ |
| e-Stat / Customs stats | STAT | 🟢 | ⚙️📦 | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇦🇺 Australia**
| ABN Lookup / ABR | ID | 🟢 | ⚙️+📦(weekly XML) | ✅ | P | rec | — | ✅ (some fields gov-only) |
| AusTender | INTENT | 🟡 | ❌ | ✅ awardees | P | rec | — | ⚠️ scrape (ToS) |
| ABS trade | STAT | 🟢 | ⚙️ | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇩🇪 Germany**
| Handelsregister (3rd-party API) | ID | 🟠 | ⚙️(vendor) | ✅ | L | lic | — | ⚠️ via licensed API (raw scrape ⛔) |
| TED (procurement) | INTENT | 🟢 | ⚙️ | ✅ | P | rec | — | ✅ |
| Destatis (GENESIS) | STAT | 🟢 | ⚙️ | ✗ | P | rec | — | ✅ |
| VIES (VAT validate) | VERIFY | 🟢 | ⚙️ | validate | Live/C | — | — | ✅ cache-only |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇫🇷 France**
| INSEE Sirene | ID | 🟢 | ⚙️+📦 | ✅ (25M) | P | **yes** | persons | ✅ |
| TED | INTENT | 🟢 | ⚙️ | ✅ | P | rec | — | ✅ |
| Douanes stats | STAT | 🟢 | ⚙️ | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇳🇱 Netherlands**
| KVK | ID | 🟡 | ⚙️ | ✅ | P/C | rec | — | ✅ (paid per call → cache) |
| TED | INTENT | 🟢 | ⚙️ | ✅ | P | rec | — | ✅ |
| CBS / Eurostat Comext | STAT | 🟢 | ⚙️📦 | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇸🇬 Singapore**
| ACRA (data.gov.sg open dataset) | ID | 🟢 | 📦 | ✅ (1.5M) | P | rec | — | ✅ |
| ACRA Marketplace (live EIQ) | ID | 🟡 | ⚙️(partner) | ✅ | C/Live | rec | — | ⚠️ partner approval |
| SingStat / Enterprise SG | STAT/INTENT | 🟢 | ⚙️ | ✗/✅ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

**🇦🇪 UAE**
| National Economic Register (NER) | ID | 🟡 | ❌ | ✅(license) | P | rec | — | ⚠️ portal |
| DIFC / ADGM public registers | ID | 🟢/🟡 | ❌ | ✅ | P | rec | — | ✅ free-zone |
| Dubai DED / ADDED | ID | 🟡 | ❌ | ✅ | P | rec | — | ⚠️ per-emirate |
| GCC-Stat | STAT | 🟡 | 📦 | ✗ | P | rec | — | ✅ |
| Mirror BoL (licensed) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

### REMAINING 20 (phase-in after priority-10)

**🇮🇳 India** — MCA21 (ID, 🟡, paid docs), DGFT/IEC (ID, 🟡 own-records), TradeStat/Commerce Dashboard (STAT, 🟢), GeM/CPPP (INTENT, 🟡, ❌ API→⚠️scrape), FIEO+EPC dirs (BUY-ish members, 🟢/🟡), mirror BoL (BUY, 🟠). Domestic customs rows ⛔ (2016). DPDP for personal.
**🇲🇽 Mexico** — SAT/SIGER (ID, 🕷️/🟡), **public customs manifests** (BUY, 🟢/🟠 — LATAM tradition, rich), Data Mexico (STAT, 🟢). Strong free/licensed named-buyer data.
**🇮🇹 Italy** — Registro Imprese/InfoCamere (ID, 🟠), VIES (verify 🟢), TED (INTENT 🟢), mirror BoL (BUY 🟠).
**🇪🇸 Spain** — Registro Mercantil (ID, 🟠), VIES (🟢), TED (🟢), mirror (🟠).
**🇧🇪 Belgium** — **KBO/BCE open extract** (ID, 🟢📦), VIES (🟢), TED (🟢), mirror (🟠).
**🇨🇭 Switzerland** — **Zefix** (ID, 🟢⚙️), Swiss customs stats (STAT 🟢), mirror (🟠). (Non-EU: no VIES.)
**🇸🇦 Saudi Arabia** — **Wathq** (ID, 🟡⚙️ gov onboarding), MoC Open Data (🟢), GASTAT/GCC-Stat (STAT 🟡), mirror (🟠).
**🇶🇦 Qatar** — MoCI registry (ID 🟡/🕷️), PSA stats + GCC-Stat (🟡), mirror (🟠).
**🇴🇲 Oman** — MoCIIP "Invest Easy" (ID 🟡), NCSI + GCC-Stat (🟡), mirror (🟠).
**🇰🇼 Kuwait** — MoCI registry (ID 🟡/🕷️), CSB + GCC-Stat (🟡), mirror (🟠).
**🇲🇾 Malaysia** — SSM (ID, 🟠 e-Info), **OpenDOSM** (STAT 🟢), MATRADE exporter dir (BUY-ish 🟢), mirror (🟠).
**🇹🇭 Thailand** — DBD DataWarehouse (ID 🟡), Customs + DITP/Thai Trade dir (BUY-ish 🟢), mirror (🟠).
**🇻🇳 Vietnam** — National Business Reg Portal (ID 🕷️/🟡), GSO stats (🟢), Customs app govt-only ⛔, mirror BoL (BUY 🟠 — main route).
**🇮🇩 Indonesia** — AHU/OSS NIB (ID 🕷️/🟡), BPS stats (🟢), INATRADE, mirror (🟠).
**🇰🇷 South Korea** — NTS BRN + data.go.kr (ID 🟡/🟢⚙️), KITA (BUY-ish, 🟠 membership), UNI-PASS (not public), mirror (🟠).
**🇳🇿 New Zealand** — **NZ Companies Register + NZBN** (ID, 🟢⚙️ very open), Stats NZ (🟢), mirror (🟠).
**🇧🇩 Bangladesh** — RJSC (ID 🕷️/🟡), EPB dir (BUY-ish), NBR stats (🟡), mirror BoL (BUY 🟠 — main route, 13.6M export recs).
**🇱🇰 Sri Lanka** — ROC (ID 🕷️/🟡), **SL Customs Online Trade Stats** (STAT 🟢), EDB exporter dir (🟢), mirror (🟠).
**🇳🇵 Nepal** — OCR (ID 🕷️), Dept of Customs stats (🟡), TEPC dir. Long-tail; mirror + stats.
**🇧🇹 Bhutan** — RSEBL/MoICE registrar (ID 🕷️), DRC customs stats (🟡). Smallest; statistics-only + mirror.

### GLOBAL / MULTILATERAL BACKBONE (all countries)
| UN Comtrade | STAT | 🟡 | ⚙️📦 | ✗ | P | **yes** | — | ✅ (corridor sizing) |
| ITC Trade Map / Market Access Map | STAT | 🟡 | ⚙️(beta) | ✗ | P/C | **yes** | — | ⚠️ API on request |
| World Bank WITS / WTO | STAT | 🟢 | ⚙️ | ✗ | P | rec | — | ✅ |
| UNGM | INTENT | 🟡 | ⚙️(OData) | ✅ | P | rec | — | ✅ |
| VIES (EU VAT) | VERIFY | 🟢 | ⚙️ | validate | Live/C | — | — | ✅ cache-only |
| OpenCorporates | ID(gap-fill) | 🟠 | ⚙️ | ✅ | L | **yes** | directors | ✅ licensed |
| OFAC/EU/UN/UK sanctions + trade.gov CSL | RISK | 🟢 | ⚙️ | ✅(flag) | P | rec | names | ✅ (must use) |
| Trade news / RSS (global) | INTENT | 🟢 | RSS | enrich | P | link | — | ✅ |
| Volza / ImportGenius (mirror BoL) | BUY | 🟠 | ⚙️ | ✅ | L | lic | — | ✅ licensed |

---

## §5. Legal roll-up for this registry (Phase-1 gate confirmations)
- **Company/entity + trade-activity data across all 30 countries: ✅ collectable, storable, displayable, monetizable** (EU registries = high-value re-usable datasets; public customs where public; licensed where not).
- **Attribution required** for: UN Comtrade, ITC, INSEE Sirene, OpenCorporates, EU open datasets, CC-BY sources → enforced via `sources.attribution_text`.
- **Cache-only:** VIES, ACRA live API, KVK per-call, any ToS-restricted KYB.
- **Licensed (store per contract):** all mirror BoL, Handelsregister 3rd-party, OpenCorporates.
- **Forbidden:** US air/truck manifests, India domestic customs rows, LinkedIn/personal scraping, bulk-republishing licensed DBs.
- **Personal data** (Sirene persons, Companies House officers, any contact) → gated `contacts` collection + lawful basis + DSAR.

## §6. What I need from you (review gate)
Please review & approve:
1. The **10K allocation** (§3) — agree with the country weighting and the single licensed feed (Volza ~$1,500) to cover confidential-import corridors?
2. The **source verdicts** (§4) — any source you want added/removed/deprioritized?
3. Confirm we **start the first 10K from free sources** (USA CBP BoL + Canada CID + registries + procurement ≈ 6,000 at ~$0) before spending on the licensed feed for the remaining ~4,000?

On approval, Phase 2 (Global Architecture) is the next prompt. The machine-readable master registry is in **`sources_seed.json`** — the single source every future connector reads from.
