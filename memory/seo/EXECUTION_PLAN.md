# Vametra AI — SEO/GEO Execution Plan
Owner-approved 7 Oct 2026. Built in small verified parts; each part is tested before the next starts.

Scope approved by owner: Phases 1+2+3 · server-side pre-rendering for SEO pages · honest
"coverage expanding + notify me" buyer panel outside Europe · products = Basmati Rice, Fresh
Vegetables, Fresh Fruits, Agarbatti, Indian Spices, Cotton Textiles & Apparel, Pharmaceuticals,
Engineering Goods & Machinery · publish strictly by data sufficiency, never by combination count.

---
## STATUS BOARD

| Part | What | Status |
|---|---|---|
| **1** | Data foundation: aggregator + sufficiency gate + refresh | ✅ **DONE 7 Oct 2026** |
| 2 | Frontend `/export/{product}/to/{country}` template + answer-first content | ⬜ next |
| 3 | Server-side pre-rendering for SEO routes (AI crawler visibility) | ⬜ |
| 4 | Geography: region hubs + country/corridor pages (Europe + Middle East + CN/UK/NL/DE/SG/SA) | ⬜ |
| 5 | Publish product × country batch 1 (gate-approved only) + full internal-link graph | ⬜ |
| 6 | Answer-first rewrites of the 47 existing pages + acceptance report (16 items) | ⬜ |

---
## PART 1 — Data foundation ✅ DONE

New module `backend/seo_pages.py`, routes under `/api/seo/`:

| Endpoint | Purpose |
|---|---|
| `GET /api/seo/catalogue` | 8 products · 56 countries · 5 regions (europe 20, middle-east 9, asia-pacific 14, americas 8, africa 4) + the gate weights |
| `GET /api/seo/page-data/{product}/{country}` | Full page payload: duty, preferential, India export benefit, world + country-specific demand, buyers, expos, news, `dataScore`, `indexable`, `sources[]`, disclaimer |
| `GET /api/seo/matrix?product=&region=` | Scores every combination, sorted; 24h cache; drives publish/noindex decisions and the sitemap |
| `POST /api/seo/refresh-all` | Admin: force-refresh WITS duty cache + RoDTEP + trade-stat cache + HS directory + news + expo engines, returns a per-source report |

**Data sufficiency gate** (mechanical, not judgement):
`duty 40 + demand 30 + buyers 15 + expos 8 + news 7`; indexable requires **score ≥ 70 AND a real
tariff record AND real demand data**. Anything below renders but is `noindex` and is never submitted
to the sitemap or IndexNow — it flips to indexable automatically when data arrives.

**Verified live on production data (no fabrication anywhere):**
- `basmati-rice → germany` score 100 · duty 0% (WITS 2023) · RoDTEP 1.0% · Germany imports **$462.7M**, world rank **20 of 222**, 1.49% share (OEC 2024) · 5,280 buyers (113 HS-matched) · 4 expos · 4 news
- `basmati-rice → uae` score 77 · UAE imports $674.3M, rank 10 · 0 buyers (honest panel)
- `agarbatti → middle-east` 9 combos in 8.5s: Saudi 5% duty/$17.7M/rank 4 · Egypt **45%** duty · Turkey 31.5% · Bahrain **score 37 → correctly NOT indexable** (no tariff record)

**Bugs fixed on the way**
- Trade Intelligence returned "No trade data found" for every HS code → stale in-memory HS directory
  (5,606 of 16,818 codes). Now resolves via Mongo and rebuilds; `follow_redirects` added (OEC members
  endpoint 307s).
- Added `trade_intel.importer_table()` / `importer_detail()` so each page shows **its own country's**
  import value, world rank and share out of 222 reporting countries — not just a global top-12 list.
  Cached 14 days.
- `matrix` ran sequentially and blew the 60s gateway limit → now concurrent (semaphore 8) + 24h cached.

---
## PART 2 — Product × country template (next)
Route `/export/{product}/to/{country}`, data from Part 1. Sections in order:
answer-first 40-60 words → trade snapshot → HS code → duty table (+ India breakdown) → FTA/preferential
→ demand & rank → documents → certifications → buyers panel (real counts in Europe, notify-me elsewhere)
→ landed-cost worked example → logistics/Incoterms → expos → news → FAQ (the 8 intents) → action panel.
Meta/H1/canonical/breadcrumbs per page; `noindex` honoured from `indexable`; schema: WebPage +
BreadcrumbList + FAQPage + Dataset. Every section links to the matching tool.

## PART 3 — Pre-rendering
Backend renders complete HTML for `/export/*`, `/countries/*`, `/corridors/*`, `/products/*`,
`/regions/*` when the request is a crawler (GPTBot, PerplexityBot, ClaudeBot, Googlebot, bingbot…),
humans keep the React app. No change to auth, DB, pricing or payments.

## PART 4 — Geography
`/regions/europe`, `/regions/middle-east` hubs + country profiles and corridors for all 20 Europe +
9 Middle East countries plus China, UK, Netherlands, Germany, Singapore, Saudi Arabia. Same gate.

## PART 5 — Publish batch 1 + link graph
Only gate-approved combinations. Full internal-link graph: product ↔ country ↔ corridor ↔ product×country
↔ HSN finder ↔ duty calculator ↔ landed cost ↔ buyers ↔ Command Center ↔ AI Brain ↔ sign-up. Zero orphans.

## PART 6 — Existing pages + acceptance report
Answer-first rewrites, title/meta/H1 per the keyword map, then the 16-item report the owner specified.

---
## BACKLOG (owner-visible; removed when done)
1. **CHA / Customs Brokers tool** — `/tools/custom-brokers` (path already locked in Clarity funnel).
   Must ship SEO-ready: own keyword cluster (customs broker, CHA, customs house agent, clearing agent
   + per-port/per-country variants), FAQ schema, links to duty calculator and compliance pages.
2. **Middle East buyer ingestion** — find and vet authentic sources so Gulf pages can show real buyers.
   Candidates to evaluate for licence + ToS: UAE/Saudi official company registries (DED, MoCI),
   GCC chamber-of-commerce member directories, customs trade registries, UN/WTO supplier rosters,
   trade-fair exhibitor lists already in our expo feeds (lawful, attributable), government tender portals.
   Sanctions screening must run before any record is published.
3. **Second authentic duty source** — WITS is the only keyless official tariff API. Adding a
   cross-check needs a **free** key: WTO Tariff & Trade Data API (api.wto.org) or ITC Market Access Map.
   Owner action: register, send key → then wire as a second source with per-field provenance.
4. **UN Comtrade key (optional)** — `COMTRADE_API_KEY` already supported; unlocks more current
   trade stats than BACI 2024 when set.
5. **Admin "Refresh all data" button** — backend `POST /api/seo/refresh-all` is live; add the button
   to the admin dashboard with the per-source report.
6. **FTA/preferential coverage** — WITS reports preferential rates unevenly; CEPA/ECTA/CECA benefits
   should be shown only where reported or sourced from the agreement text.
7. **Expo/news country matching** — currently exact country-name match; add alias mapping
   (UAE/United Arab Emirates/Dubai) so more pages pick up real events and news.
