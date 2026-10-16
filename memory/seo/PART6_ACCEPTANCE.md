# PART 6 — Acceptance report (preview, 16 Oct 2026) — pending production deploy

Scope: 27 hub pages + 44 detail pages (11 services, 5 countries, 4 corridors, 5 products, 8 industries, 9 courses, 6 posts).
Evidence: testing-agent iteration_75 (29 pages, 6 endpoints) + node title-length check + curl.

| # | Item | Result | Evidence / note |
|---|---|---|---|
| 1 | One primary keyword per page, no two pages on the same term | PASS | `PART6_PAGE_PLAN.md` + `data/seoTitles.js`; /ai-assistant keeps only AI-intent terms |
| 2 | Title ≤60 chars, keyword first, brand last | PASS | 23 hubs ≤60 (agent); all detail templates ≤60 after `clampTitle` + short names (UAE/USA/Textiles) |
| 3 | Exactly one `<title>` / one `<h1>` per page | PASS | 29/29 pages single title + single H1 |
| 4 | H1 contains the primary keyword verbatim | PASS | e.g. "Custom duty calculator India — …", "Export from India to UAE — …" |
| 5 | Meta description ≤155, answers the query, contains a number | PASS (spot) | numbers: 56 countries / 5,606 codes / 32 countries / 2026 |
| 6 | Answer-first opening (40–60 words) before marketing copy | PASS | `AnswerFirst` on 22 hubs + 6 detail templates; /pricing, /blog, index pages title/H1 only |
| 7 | One dated, citable data block with "as of" + source | PASS | `/api/seo/facts` live counts; "As of October 2026 · Source: …" row |
| 8 | No fabricated figures / no raw `{token}` placeholders | PASS | agent: 0 placeholders on 29 pages; fallbacks = production-verified figures |
| 9 | FAQ block → `FAQPage` JSON-LD, visible text == schema text | PASS | FAQPage on /tools/*, /tools, /buyers, /brain, /customs-compliance, /countries, services detail; both filled from the same facts |
| 10 | `BreadcrumbList` on every non-home page | PASS | 28/28 (home excluded by design) |
| 11 | Internal links: ≥3 money pages + 1 tool + 1 country/corridor | PASS | 5 links per AnswerFirst block |
| 12 | Soft-404 hardening: transient API error never renders "not found"; real 404 carries noindex | PASS | `loadEntity()` on 8 detail templates; 4/4 unknown slugs → not-found H1 + `noindex` |
| 13 | Loading-state snapshot carries the final title/H1 | PASS | loading branches now use the same `seoTitles` builders |
| 14 | No false app / download / "195 countries" / 2025 claims | PASS | 0 hits for "195" on /, /about, /tools, /buyers; CTARow "Download app" removed; llms.txt platforms fixed |
| 15 | Thin seeded directories not indexable | PASS | /suppliers & /directory already redirect home; /directory/:kind now `noindex`; none in sitemap |
| 16 | Production Googlebot render of all rewritten URLs (200, >150 words, 1 title) | PENDING DEPLOY | run `memory/audit_2026-10-10/guides_audit.py`-style pass over the 71 URLs after deploy; prerender warm now covers 56 key pages every 45 min |

Not verifiable in preview by browser (platform "Preview Unavailable" interstitial for headless browsers; API-backed detail pages confirmed via title/H1 and code review only): full rendered content of /countries/*, /corridors/*, /products/*, /industries/*, /academy/*, /services/*. Re-check on production after deploy.

Known deltas vs the approved plan: `/countries`, `/products`, `/industries` titles end "| Vametra" (brand shortened to fit 60); `/pricing`, `/blog` and the four index pages received title/H1 only (they already had AnswerBlock/FAQ content).
