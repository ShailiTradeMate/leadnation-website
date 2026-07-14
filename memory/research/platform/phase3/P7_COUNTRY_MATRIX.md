# VBIE Phase 3 — Doc 3/6: Country-wise Connector Matrix (30 countries)
## (Deliverable 3: Country-wise Connector Matrix · Section 3: Country Intelligence)

> Architecture reference. Per source: **Method** (API/CSV/RSS/OCR/HTML/Manual) · **Refresh** · **Est. buyers (first wave)** · **Quality** (H/M/L) · **Legal** (✅allowed/⚠️restricted/⛔forbidden) · **Commercial use** (✅/lic).
> Aggregate-only stats sources are marked STAT (buyers=0; used for corridor sizing/validation). Registries = identity backbone. Named-buyer sources drive the 10K.

Legend method: A=API, C=CSV/bulk, X=XML, R=RSS, O=OCR/PDF, H=HTML-crawl, M=manual/partner.

---
## PRIORITY 10

### 🇺🇸 USA
| Source | Method | Refresh | Est.buyers | Quality | Legal | Comm |
|--------|:--:|--------|:--:|:--:|:--:|:--:|
| CBP ocean BoL (FOIA/vendor) | C/O | weekly | 3,000 | H | ✅ | ✅ |
| SAM.gov entity+opps | A | daily | 1,000 | H | ✅ | ✅ |
| USITC DataWeb/Census (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| trade.gov CSL (risk) | A | daily | — | H | ✅ | ✅ |
| State registries | H/A | event | — | M | ⚠️ | ✅ |

### 🇨🇦 Canada
| Canada CID | C | monthly | 1,000 | H | ✅ | ✅ |
| Corporations Canada | A | weekly | 300 | H | ✅ | ✅ |
| CIMT (STAT) | A/C | monthly | 0 | H | ✅ | ✅ |
| CanadaBuys | A | daily | 200 | M | ✅ | ✅ |

### 🇬🇧 UK
| Companies House | A+Webhook | daily | 400 | H | ✅ | ✅ |
| Contracts Finder/FTS | A | daily | 300 | H | ✅ | ✅ |
| HMRC Trade Info (STAT) | A/C | monthly | 0 | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 200 | M | ✅ | lic |

### 🇯🇵 Japan
| gBizINFO (incl. gov contracts) | A | monthly | 400 | H | ✅ | ✅ |
| Corporate Number API | A | monthly | 100 | H | ✅ | ✅ |
| e-Stat/Customs (STAT) | A/C | monthly | 0 | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 200 | M | ✅ | lic |

### 🇦🇺 Australia
| ABN Lookup/ABR | A+X(bulk) | weekly | 300 | H | ✅ | ✅ |
| AusTender | H | daily | 200 | M | ⚠️ | ✅ |
| ABS trade (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 100 | M | ✅ | lic |

### 🇩🇪 Germany
| TED (procurement) | A | daily | 300 | H | ✅ | ✅ |
| Handelsregister (3rd-party) | A(lic) | event | 200 | M | ⚠️ | lic |
| Destatis (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| VIES (verify) | A | on-demand | — | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 100 | M | ✅ | lic |

### 🇫🇷 France
| INSEE Sirene | A+C | daily | 300 | H | ✅(attrib) | ✅ |
| TED | A | daily | 150 | H | ✅ | ✅ |
| Douanes (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 50 | M | ✅ | lic |

### 🇳🇱 Netherlands
| KVK | A | daily(cache) | 250 | H | ✅ | ✅ |
| TED | A | daily | 150 | H | ✅ | ✅ |
| CBS/Comext (STAT) | A/C | monthly | 0 | H | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 100 | M | ✅ | lic |

### 🇸🇬 Singapore
| ACRA open dataset | C | monthly | 250 | H | ✅ | ✅ |
| ACRA Marketplace (live) | A(partner) | on-demand | — | H | ⚠️ | ✅ |
| SingStat/EnterpriseSG | A | monthly | 50 | M | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 100 | M | ✅ | lic |

### 🇦🇪 UAE
| NER + DIFC/ADGM registries | H/A | event | 150 | M | ⚠️ | ✅ |
| GCC-Stat (STAT) | C | monthly | 0 | M | ✅ | ✅ |
| Mirror BoL (optional) | A(lic) | weekly | 250 | M | ✅ | lic |

**Priority-10 free-first subtotal ≈ 6,000+ buyers at $0** (excludes optional mirror rows).

---
## REMAINING 20 (phase-in)

### 🇮🇳 India (flagship)
| MCA21 registry | H/A | event | — | M | ⚠️ | ✅ |
| DGFT/IEC | A | event | — | M | ⚠️ | ✅ |
| TradeStat/Commerce Dashboard (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| GeM/CPPP | H | daily | ✓ | M | ⚠️ | ✅ |
| FIEO+EPC dirs | H/M | monthly | ✓ | M | ⚠️ | ✅ |
| Domestic customs | — | — | 0 | — | ⛔ | — |
| Mirror BoL (optional) | A(lic) | weekly | ✓ | M | ✅ | lic |

### 🇲🇽 Mexico
| Public customs manifests | C | monthly | H-yield | H | ✅ | ✅ |
| SAT/SIGER registry | H | event | — | M | ⚠️ | ✅ |
| Data Mexico (STAT) | A | monthly | 0 | H | ✅ | ✅ |

### 🇮🇹 Italy
| Registro Imprese | A(lic) | event | — | M | ⚠️ | lic |
| TED | A | daily | ✓ | H | ✅ | ✅ |
| VIES (verify) | A | on-demand | — | H | ✅ | ✅ |

### 🇪🇸 Spain
| Registro Mercantil | A(lic) | event | — | M | ⚠️ | lic |
| TED | A | daily | ✓ | H | ✅ | ✅ |
| VIES | A | on-demand | — | H | ✅ | ✅ |

### 🇧🇪 Belgium
| KBO/BCE open extract | C | daily | ✓ | H | ✅ | ✅ |
| TED | A | daily | ✓ | H | ✅ | ✅ |

### 🇨🇭 Switzerland
| Zefix | A | daily | ✓ | H | ✅ | ✅ |
| Swiss customs (STAT) | A | monthly | 0 | H | ✅ | ✅ |

### 🇸🇦 Saudi Arabia
| Wathq CR API | A | realtime | ✓ | H | ⚠️(onboard) | ✅ |
| MoC Open Data | C | monthly | ✓ | M | ✅ | ✅ |
| GASTAT/GCC-Stat (STAT) | C | monthly | 0 | M | ✅ | ✅ |

### 🇶🇦 Qatar / 🇴🇲 Oman / 🇰🇼 Kuwait
| MoCI/MoCIIP registries | H | event | ✓ | M | ⚠️ | ✅ |
| National stats + GCC-Stat (STAT) | C | monthly | 0 | M | ✅ | ✅ |

### 🇲🇾 Malaysia
| SSM (paid) | A(lic) | event | — | M | ⚠️ | lic |
| OpenDOSM (STAT) | C | monthly | 0 | H | ✅ | ✅ |
| MATRADE exporter dir | H/M | monthly | ✓ | M | ⚠️ | ✅ |

### 🇹🇭 Thailand
| DBD DataWarehouse | H/A | event | ✓ | M | ⚠️ | ✅ |
| DITP/Thai Trade dir | H/M | monthly | ✓ | M | ⚠️ | ✅ |

### 🇻🇳 Vietnam
| National Business Reg Portal | H | event | ✓ | M | ⚠️ | ✅ |
| GSO (STAT) | A/C | monthly | 0 | M | ✅ | ✅ |
| Mirror BoL (main route) | A(lic) | weekly | ✓ | M | ✅ | lic |

### 🇮🇩 Indonesia
| AHU/OSS (NIB) | H | event | ✓ | M | ⚠️ | ✅ |
| BPS (STAT) | A | monthly | 0 | M | ✅ | ✅ |

### 🇰🇷 South Korea
| NTS BRN + data.go.kr | A | event | ✓ | M | ⚠️ | ✅ |
| KITA (membership) | M | — | ✓ | M | ⚠️ | lic |

### 🇳🇿 New Zealand
| NZ Companies Register + NZBN | A | daily | ✓ | H | ✅ | ✅ |
| Stats NZ (STAT) | A | monthly | 0 | H | ✅ | ✅ |

### 🇧🇩 Bangladesh
| RJSC registry | H | event | ✓ | L | ⚠️ | ✅ |
| EPB dir | H/M | monthly | ✓ | M | ⚠️ | ✅ |
| Mirror BoL (main route) | A(lic) | weekly | ✓ | M | ✅ | lic |

### 🇱🇰 Sri Lanka
| ROC registry | H | event | ✓ | L | ⚠️ | ✅ |
| SL Customs Online Stats (STAT) | H | monthly | 0 | M | ✅ | ✅ |
| EDB exporter dir | H | monthly | ✓ | M | ⚠️ | ✅ |

### 🇳🇵 Nepal / 🇧🇹 Bhutan
| OCR/RSEBL registrars | H/O | event | long-tail | L | ⚠️ | ✅ |
| Customs stats (STAT) | H/O | monthly | 0 | L | ⚠️ | ✅ |

---
## GLOBAL BACKBONE (all countries)
| UN Comtrade (STAT) | A | monthly | 0 | H | ✅(attrib) | ✅ |
| ITC Trade Map (STAT) | A(beta) | monthly | 0 | H | ⚠️ | ⚠️ |
| WITS/WTO (STAT) | A | monthly | 0 | H | ✅ | ✅ |
| UNGM (procurement) | A(OData) | daily | ✓ | H | ✅ | ✅ |
| VIES (verify) | A | on-demand | — | H | ✅ | ✅ |
| Sanctions/CSL (risk) | A | daily | — | H | ✅ | ✅ |
| OpenCorporates (gap-fill) | A(lic) | varies | ✓ | H | ✅ | lic |
| Mirror BoL adapters | A(lic) | weekly | ✓ | M | ✅ | lic |
| Trade award winners / delegations | R/O | per_event | ✓ | M | ✅/⚠️ | ✅ |
| Trade fair exhibitors | H/M | per_event | ✓ | M | ⚠️ | ✅ |
| Company websites / news | H/R | monthly/daily | enrich | M | ✅ | ✅ |
| Claim-this-Company | A(internal) | event | ✓ | H | ✅ | ✅ |

**Expansion rule:** any new country = new `sources` entries reusing existing connector types. No new architecture.
