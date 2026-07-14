# Phase 1 — Registry Addendum (approved updates incorporated)

This addendum records the changes approved after the initial Phase 1 registry. The machine-readable `sources_seed.json` has been updated accordingly (now 50 sources).

## 1. FREE-FIRST strategy locked
Target: **~6,000+ verified buyers from free, official, legally-reusable sources BEFORE any licensed provider is activated.**
Free-first buyer engines (all $0):
- 🇺🇸 US CBP ocean BoL + SAM.gov awardees → ~4,000
- 🇨🇦 Canada CID + Corporations Canada → ~1,500
- Procurement awards: TED (EU), Contracts Finder (UK), AusTender (AU), gBizINFO gov-contracts (JP), UNGM → ~1,500
- Registries (UK/FR/JP/SG/AU/BE/CH/NZ) → identity/verification backbone
- **New** trade-promotion sources (below) → verified members + intent
Licensed mirror BoL is **deferred** and **provider-agnostic** (see §3).

## 2. New sources added to the registry (approved update #3)
| source_id | What it adds | Names buyers | Verdict |
|-----------|--------------|:---:|:---:|
| `embassy_commercial_wings` | Embassy commercial sections / TFO importer & trade-lead lists | ✅ | restricted (partnership-preferred) |
| `epc_directories` | Export Promotion Council member directories (APEDA/EEPC/CHEMEXCIL/Pharmexcil/GJEPC/CAPEXIL + MATRADE/DITP/EDB/EPB) | ✅ | restricted (ToS/MoU) |
| `chambers_of_commerce` | National + bilateral chambers + ICC | ✅ | restricted |
| `industry_associations` | Sector import/export associations | ✅ | restricted |
| `trade_fair_exhibitors` | Expo/trade-fair exhibitor & visitor directories | ✅ | restricted (organizer partnership) |
| `trade_award_winners` | Export/trade award winners (public announcements) | ✅ | **allowed** (RSS/press) |
| `trade_delegation_lists` | Official trade-mission/delegation participant lists | ✅ | restricted (high trust/intent) |
| `gem_cppp_india` | India GeM/CPPP procurement | ✅ | restricted (ToS crawl) |
| `eu_ted_global` | Single TED connector for all EU corridors | ✅ | allowed |
| `claimed_company_data` | **Claim-this-Company** self-verified profiles (consent) | ✅ | **allowed** (highest freshness) |

**Legal handling for member/exhibitor directories:** most are ToS-restricted → **prefer partnership/MoU over scraping**; any personal contacts route into the gated `contacts` pipeline under lawful basis. Award winners & delegation lists (often press/RSS) are cleaner to reuse with attribution.

## 3. Licensed providers = interchangeable modules (approved update #2)
No single provider (esp. Volza) is a hard dependency. The connector layer defines a **`MirrorBoLProvider` interface** with pluggable adapters: `volza`, `importgenius`, `panjiva`, `datamyne`. Any/none can be enabled per-corridor via the `sources` registry (`active` flag). See Phase 2 §4. Comparison for a future licensing decision: `PROVIDER_COMPARISON.md`.

## 4. Product updates carried into Phase 2
- **#4 Claim-this-Company workflow** — added as source `claimed_company_data` + designed in Phase 2 §7.
- **#5 Source Evidence section** — mandatory on every Buyer Intelligence Card; designed in Phase 2 §6 (backed by the `provenance` ledger).
- **#6 AI Match Score (exporter↔buyer)** — planned as a post-MVP module in Phase 2 §8; explicitly **excluded from MVP**.
