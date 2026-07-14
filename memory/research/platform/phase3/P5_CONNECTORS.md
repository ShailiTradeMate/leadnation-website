# VBIE Phase 3 — Doc 1/6: Connector Framework + Source Connector Matrix + Future-Ready Plugins
## (Deliverable 1: Connector Architecture · Deliverable 4: Source Connector Matrix · Section 12: Future Ready)

> **Status:** Architecture/blueprint only. NO production code. For review before Phase 4.

---

## SECTION 1 — CONNECTOR FRAMEWORK

### §1.1 Design goal
One **modular, hot-swappable, provider-agnostic, country-agnostic** ingestion framework. Adding a country or provider = adding a `sources` registry entry + (maybe) a config, never re-architecting.

### §1.2 The common Connector interface (contract every connector implements)
```
interface Connector:
  # lifecycle
  validate_config(source: SourceRegistryEntry) -> ok|errors
  can_run(now, source) -> bool            # cadence + quota + legal gate
  discover() -> Iterator[RawRef]          # list new/changed items (delta-aware)
  fetch(ref: RawRef) -> RawPayload        # get one item
  parse(payload) -> Iterator[CanonicalEvent]   # normalize to schema
  emit(events) -> writes raw_records (+provenance) & candidates
  health() -> ConnectorHealth
  # every method is idempotent + provenance-stamping + legal-flag-aware
```
Shared cross-cutting services injected into every connector: **ProvenanceStamper, LegalGate (reads `sources` verdict/license/personal flags), RateLimiter, RetryPolicy, Deduper (content hash), Translator, SecretResolver**.

### §1.3 Connector types (all implement the interface)
| Connector | Protocol/Input | Primary use | Notes |
|-----------|----------------|-------------|-------|
| **GovernmentAPIConnector** | REST / SOAP / GraphQL / OData | Companies House, SAM.gov, Comtrade, TED, UNGM, gBizINFO, ABN, Sirene, VIES | Auth via SecretResolver; pagination; OData for UNGM |
| **CSVConnector** | CSV / TSV | ABN bulk XML→csv, Canada CID, ACRA open data, OpenDOSM | Streaming parse; schema map per source |
| **ExcelConnector** | XLSX / XLS | GCC-Stat, national stats releases | Sheet/range mapping |
| **XMLConnector** | XML feeds | ABN weekly bulk, gov feeds | XSD-aware |
| **RSSConnector** | RSS / Atom | Trade news, award winners, tender feeds | Cheapest change-detection; preferred |
| **PDFConnector** | PDF (text layer) | Gov publications, delegation lists | Text extract → parse |
| **OCRConnector** | Scanned PDF / image | Embassy lists, trade-fair brochures | OCR → AI extraction (Section 4) |
| **HTMLConnector** | Static/rendered HTML | Registry pages w/o API, directories (ToS-permitting) | Uses SmartCrawler (Section 2) |
| **SitemapConnector** | sitemap.xml | File/page discovery on large gov sites | Feeds crawler queue |
| **WebhookConnector** | inbound push | Companies House streaming, future partner pushes | Event-driven, near-real-time |
| **CommercialProviderConnector** | vendor API | OpenCorporates, KYB vendors | License-gated; store per contract |
| **MirrorBoLConnector** | vendor API | Volza/ImportGenius/Panjiva/Datamyne adapters | Interface + adapters (§12) |
| **ClaimConnector** | internal API | Claim-this-Company consented data | Lawful basis = consent |
| **FutureAIConnector** | agentic | LLM-driven discovery of new sources/pages | Candidates only; human-review gate |

### §1.4 Hot-swappability & configuration
- Every connector instance is bound to a `sources` registry entry (`source_id`).
- **Enable/disable = flip `active` flag**; no deploy. **Swap provider = point `MirrorBoLConnector` at a different adapter.**
- Connector *type* selected by `sources.api` + `category`; the framework instantiates the right class via a registry/factory.
- Legal behavior (store/cache/attribution/personal) comes from the `sources` entry → connectors never hardcode policy.

### §1.5 Connector state machine
`IDLE → SCHEDULED → DISCOVERING → FETCHING → PARSING → EMITTING → DONE` (with `RETRYING`, `RATE_LIMITED`, `HALTED_LEGAL`, `FAILED`). Every transition logged to `crawler_logs`/`connector_runs`.

---

## SECTION 12 — FUTURE READY (plugin model)

### §12.1 Plugin principle
Any current or future source (Companies House, ABR, ACRA, VIES, gBizINFO, Trade.gov, UN Comtrade, UNGM, TED, Volza, Datamyne, Panjiva, ImportGenius, or unknown-2027-provider) is enabled by:
1. Add a **`sources` registry entry** (access/api/license/attribution/personal/cadence/verdict).
2. Pick an existing **connector type** (or register a new adapter implementing the interface).
3. Provide credentials via **SecretResolver** (env only).
4. Set `active:true`.
No core architecture change — ever.

### §12.2 Provider adapter registry (example, provider-agnostic)
```
MirrorBoLProvider (interface): search(corridor, hs, date_range) -> ShipmentEvent[]
  ├ VolzaAdapter        active:false
  ├ ImportGeniusAdapter active:false
  ├ PanjivaAdapter      active:false
  └ DatamyneAdapter     active:false
Registry (interface): lookup(country, reg_id|name) -> RegistryRecord
  ├ CompaniesHouseAdapter · SireneAdapter · gBizInfoAdapter · ABNAdapter · ACRAAdapter · OpenCorporatesAdapter ...
```
Adapters are versioned; a broken adapter can be disabled without affecting others (failure isolation).

---

## DELIVERABLE 4 — SOURCE CONNECTOR MATRIX (source → connector type → policy)
Driven by `sources_seed.json`. Method: API/CSV/XML/RSS/OCR/HTML/Webhook. Store: P=permanent/C=cache/L=licensed/Live.

| Source | Connector type | Method | Refresh | Store | Attribution | Personal gate | Verdict |
|--------|----------------|--------|---------|:--:|:--:|:--:|:--:|
| UK Companies House | GovernmentAPI + Webhook(stream) | REST + stream | daily/rt | P | rec | officers→gate | ✅ |
| US CBP ocean BoL | CSV/PDFConnector (FOIA/vendor) | bulk | weekly | P | rec | — | ✅ |
| SAM.gov | GovernmentAPI | REST | daily | P | Source:SAM.gov | — | ✅ |
| Canada CID | CSVConnector | bulk | monthly | P | Source:ISED | — | ✅ |
| Corporations Canada | GovernmentAPI | REST | weekly | P | rec | officers→gate | ✅ |
| INSEE Sirene | GovernmentAPI + CSV | REST/bulk | daily | P | **yes** | persons→gate | ✅ |
| gBizINFO | GovernmentAPI | REST | monthly | P | **yes** | — | ✅ |
| ABN Lookup | GovernmentAPI + XML | REST/bulk XML | weekly | P | **yes** | — | ✅ |
| ACRA open data | CSVConnector | bulk | monthly | P | **yes** | — | ✅ |
| UN Comtrade | GovernmentAPI | REST | monthly | P | **yes** | — | ✅ |
| TED (EU) | GovernmentAPI | REST/SPARQL | daily | P | rec | — | ✅ |
| UNGM | GovernmentAPI | OData | daily | P | rec | — | ✅ |
| trade.gov CSL / sanctions | GovernmentAPI | REST | daily | P | rec | names | ✅ (mandatory) |
| VIES | GovernmentAPI | SOAP/REST | on-demand | **C(7d)** | — | — | ✅ cache-only |
| Contracts Finder (UK) | GovernmentAPI | REST | daily | P | rec | — | ✅ |
| AusTender | HTMLConnector (SmartCrawler) | HTML | daily | P | yes | — | ⚠️ ToS-gated |
| GeM/CPPP (IN) | HTMLConnector | HTML | daily | P | yes | — | ⚠️ ToS-gated |
| Handelsregister (DE) | CommercialProvider (3rd-party API) | REST | event | **L** | vendor | officers→gate | ⚠️ licensed |
| OpenCorporates | CommercialProvider | REST | varies | **L** | **yes** | officers→gate | ✅ licensed |
| EPC / chamber / industry dirs | HTMLConnector / partner feed | HTML/CSV | monthly | P | **yes** | contacts→gate | ⚠️ ToS/MoU |
| Embassy commercial wings | PDF/OCR/HTMLConnector | PDF/HTML | quarterly | P | yes | contacts→gate | ⚠️ partnership |
| Trade delegation lists | PDF/OCRConnector | PDF/OCR | per_event | P | yes | contacts→gate | ⚠️ |
| Trade fair exhibitors | HTMLConnector / partner | HTML | per_event | P | yes | contacts→gate | ⚠️ organizer partnership |
| Trade award winners | RSSConnector | RSS/press | per_event | P | yes | — | ✅ |
| Trade news | RSSConnector | RSS | daily | P | link | — | ✅ |
| Company websites | HTMLConnector (SmartCrawler) | HTML | monthly | P | link | contacts→gate | ✅ robots |
| Claim-this-Company | ClaimConnector | internal | event | P | self | consent | ✅ |
| Volza/ImportGenius/Panjiva/Datamyne | MirrorBoLConnector (adapters) | REST | weekly | **L** | lic | contacts→gate | ✅ licensed, off by default |
| LinkedIn people | — | — | — | — | — | — | ⛔ FORBIDDEN |

**Rule enforced by framework:** a connector cannot emit to the visible graph if its `sources.verdict=forbidden`, and it cannot store personal data unless a lawful basis is attached.
