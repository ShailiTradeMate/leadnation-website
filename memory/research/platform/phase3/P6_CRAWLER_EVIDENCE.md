# VBIE Phase 3 — Doc 2/6: Advanced Smart Crawler + Evidence Engine
## (Deliverable 2: Crawler Architecture · Section 6: Evidence Engine)

> Architecture only. NO code. The crawler is an *intelligence collector for legally-reusable official data*, not a scraper.

---

## SECTION 2 — ADVANCED SMART CRAWLER

### §2.1 Non-negotiable posture
The crawler exists to fetch **public, legally-reusable** content where no API/bulk exists. It **never** defeats access controls, logs in to gated data, or touches `verdict=forbidden` sources. Legality is checked *before* every fetch.

### §2.2 Crawler subsystems
```
[Legal Gate] → [Frontier/Queue] → [Scheduler] → [Fetcher pool] → [Renderer?] →
[Extractor] → [Delta/Hash] → [Normalizer] → [Provenance] → raw_records/candidates
                     ▲                                   │
                     └──────── [Change detector] ────────┘
```

| Subsystem | Responsibility |
|-----------|----------------|
| **Legal Gate** | Per-domain allowlist; reads `sources.verdict/crawler/tos_url`; blocks unless `allowed_robots`/`tos_gated`(approved). robots.txt + crawl-delay parsed & cached |
| **Frontier/Queue** | URL frontier with priority + politeness (per-domain buckets) |
| **Scheduler** | Priority scheduling (high-value corridors first), quota-aware, per-domain rate caps |
| **Fetcher pool** | Distributed workers; connection reuse; ETag/Last-Modified conditional GET |
| **Renderer** | Headless render only for JS-heavy pages (opt-in per source; expensive) |
| **Extractor** | Structured-data-first: JSON-LD → schema.org → OpenGraph → microdata → AI fallback |
| **Delta/Hash** | Content hashing (SHA-256 of normalized content) → skip unchanged; version on change |
| **Change detector** | Sitemap lastmod, HTTP conditional headers, hash diff |
| **Normalizer** | Canonical event schema + language normalization |
| **Provenance** | Stamps source URL + fetch_ts + parser version (Section 6) |

### §2.3 Capability checklist → design
| Capability | Design |
|-----------|--------|
| robots.txt validation | Parsed + cached per host; disallow respected; crawl-delay honored |
| ToS awareness | `sources.tos_url` reviewed → domain allowlist; `verdict` gates |
| Country legal policy | Legal Gate reads country policy (GDPR/DPDP/etc.) → personal data quarantined |
| Rate limiting | Token-bucket per domain; global concurrency cap; adaptive on latency |
| Adaptive crawling | Slow down on 429/latency spikes; speed up when healthy |
| Retry strategy | Exponential backoff + jitter; max attempts; dead-letter after N |
| Distributed crawling | Stateless fetchers + shared queue (horizontal scale) |
| Queue management | Priority + politeness queues (Section 7/Queue doc) |
| Incremental crawling | Conditional GET + sitemap lastmod + hash |
| Delta detection | Hash diff vs last snapshot |
| Content hashing | Normalized-content SHA-256 stored per URL |
| Duplicate detection | URL canonicalization + content-hash dedupe |
| Version history | New snapshot on hash change; old retained (audit) |
| Automatic resume | Checkpointed frontier; resume from last cursor |
| Priority scheduling | Corridor value × source buyer_yield × staleness |
| Multilingual crawling | Charset/lang detection; locale-aware parsing |
| Dynamic rendering | Headless render gated per source (cost-controlled) |
| Structured extraction | JSON-LD/schema.org/OG/microdata parsers |
| Metadata/OpenGraph/JSON-LD | Dedicated extractors, ranked by reliability |
| File discovery | Sitemap + link analysis → PDF/CSV/XML queues |
| Gov archive discovery | Crawl document repositories; route files to PDF/CSV/OCR connectors |
| Language detection + translation | Detect → translate pipeline before extraction (Section 4) |
| AI-assisted extraction | LLM fallback for unstructured pages → structured JSON (Section 4) |

### §2.4 Politeness & ethics defaults
- Honest User-Agent with contact URL. Conservative default rate (e.g. ≤1 req/s/domain unless higher permitted).
- Cache aggressively; never re-fetch unchanged. Auto-halt on 403/429/legal signal.
- No proxy use to bypass access controls (CFAA/anti-circumvention risk).

### §2.5 Extraction reliability ladder (prefer structured over AI)
`JSON-LD → schema.org microdata → OpenGraph meta → table/DOM heuristics → AI/LLM extraction (last resort, evidence-captured)`. AI output is always a *candidate* requiring validation (Section 4/5).

---

## SECTION 6 — EVIDENCE ENGINE (no field without provenance)

### §6.1 Principle
Every stored attribute carries a **provenance record**. A value with no provenance is **rejected at write time.** This is enforced in the write path, not by convention.

### §6.2 Provenance record (per attribute value)
```
ProvenanceRecord {
  entity_id, attribute_path,        # e.g. entities/123 . website
  value,                            # the value this evidence supports
  original_source (source_id),      # from sources registry
  source_url,                       # exact URL/endpoint/doc
  collection_date,                  # first fetched
  refresh_date,                     # last re-verified
  confidence (0-1),                 # source_trust × recency × corroboration
  license_type, attribution_text,   # from sources registry
  verification_method,              # api|bulk|crawl|ocr+ai|human_qa|owner_claim|sanctions_screen
  country, legal_policy,            # GDPR|DPDP|open_attribution|foia|consent...
  extractor_version, raw_record_ref # reproducibility
}
```

### §6.3 Write-path enforcement
```
setAttribute(entity, path, value, provenance):
  assert provenance.original_source in sources_registry
  assert provenance.source_url present
  if sources[source].personal_data != none: assert lawful_basis attached
  if sources[source].verdict == forbidden: REJECT
  append to provenance ledger (immutable)
  update attribute {value, confidence, sources:[...], first_seen, last_verified}
```

### §6.4 How Evidence powers the product
- **Buyer Card "Source Evidence" panel** = a rendered view of provenance (source, date, method, link, attribution). Mandatory on every card.
- **AEO/LLM citability** — machine-readable provenance is exactly what AI engines cite.
- **Audit & DSAR** — provenance + immutable `raw_records` reconstruct exactly what was known, when, from where.
- **Trust calibration** — confidence per attribute rolls into the Trust Score.

### §6.5 Attribution automation
Attribution text is stored on the `sources` entry and auto-rendered wherever the attribute appears (UN Comtrade, INSEE Sirene, gBizINFO, ITC, CC-BY sources). Licensed data shows evidence-of-existence per license, never verbatim resale.
