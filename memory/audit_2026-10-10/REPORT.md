# Production verification report — 10 Oct 2026 (22:00–23:00 UTC), target https://vametra.com

## 1. What is deployed vs. not
| Change | Production? | Evidence |
|---|---|---|
| page-data Mongo cache + warm job + WITS gate (yesterday) | YES | page-data p50 ≈ 0.15–0.25 s; `cachedAt` 17:xx/18:xx UTC on most entries |
| Product→Thing schema, single title/description, breadcrumb `/export/...`, `/api/answers/index.html` | NO | prod HTML still has 2× `<title>`, breadcrumb still `/products/...`, index.html → 404 |
| Rail links only to existing country profiles/corridors (today) | NO | prod guide still links `/countries/chile` → "Country not found" |
| Stale-while-revalidate + retrying warm every 6 h (today) | NO | prod had 11 cold page-data holes (2.4–68 s) |
29/29 pytest = preview regression only. Nothing above counts as production-verified until deployed and re-audited.

## 2. Full Googlebot-UA render audit (392 guides + 15 hubs) — `guides_by_product.csv`
product,total,rendered,partial,shell,redirect,failure,http_4xx_5xx
agarbatti,49,48,0,1,0,0,0
basmati-rice,49,46,0,3,0,0,0
cotton-textiles,49,48,0,1,0,0,0
engineering-machinery,49,47,0,2,0,0,0
fresh-fruits,49,49,0,0,0,0,0
fresh-vegetables,49,48,0,1,0,0,0
indian-spices,49,46,0,3,0,0,0
pharmaceuticals,49,49,0,0,0,0,0
hubs,15,14,1,0,0,0,0
ALL,407,395,1,11,0,0,0
- 407/407 HTTP 200; 0 redirects/4xx/5xx/timeouts. Guides: 381 rendered / 11 shell (97.2 %). The 1 "partial" is `/regions` (rendered, 316 words — an index page).
- Shells: agarbatti→denmark; basmati-rice→canada, china, colombia; cotton-textiles→finland; engineering-machinery→italy, spain; fresh-vegetables→bangladesh; indian-spices→chile, czechia, mexico.
- Cause: each shell coincided with a cold page-data hole (2.4–68 s on prod). The edge then cached the shell (`x-rendered-by: crawler-cache`, `cache-control: max-age=3600`); all 11 now return in 100–400 ms with no `<h1>` even though page-data is warm. Shells are sticky until the edge cache expires/purges.
- Rendered guides: 396/396 canonical correct, 0 noindex, but 2× title / 2× description on every one (fix pending deploy), Product schema present on 381 (fix pending deploy).

## 3. /export/indian-spices (prod, Googlebot UA) — OK
200 in 6.1 s, h1 "Export Indian Spices", canonical = self, robots index, BreadcrumbList Home→/export→/export/indian-spices, visible crumb → /export, 49 guide links, 1,092 words. Only defect: duplicate `<title>` (pending deploy).

## 4. Answer documents (413) — `answers_per_doc.csv`, `answers_summary.json`
413/413 HTML 200 (p50 113 ms, max 308 ms); 413/413 Markdown 200; canonical = human page 413/413 (exactly one each); robots index,follow 413/413; one `<h1>` 413/413; all 413 HTML docs and all 413 human pages are in the sitemap; every doc links its page + markdown twin.
Data: WITS/TRAINS cited 409, OEC/Comtrade 407, DGFT/RoDTEP 394, duty % 406, USD figures 405, HS code 400, "verify/confirm" caveat 410. 0 exact duplicates; 277 distinct templates across 413 (largest group 11) — product×country guides are intentionally templated but every one carries its own numbers.
Freshness: tariff year 2023 for 334 docs, 2021 for 42, 2022 for 8, 2019 for 8 (all Egypt — WITS latest reported year); the year is printed next to every rate. Future years (2027/2028) are expo dates, not data years.
Thin: 8 tool/brain docs are 97–193 words (they describe a tool, not a market). Guides are 200–350 words; hubs up to 948.
False positives checked: "lorem" = "ad-valorem"; md/h1 mismatch = `&amp;` encoding.

## 5. page-data vs pagedata (prod, 2 runs each)
`/api/seo/page-data/pharmaceuticals/germany` → 200, 0.24 s / 0.15 s. `/api/seo/pagedata/...` → 404 `{"detail":"Not Found"}`, 0.19 s / 0.16 s. The hyphenated path is the only route; `pagedata` never existed.
Full sweep of all 392 sitemap guides' page-data: 392/392 HTTP 200; 11 were cold (>2 s) and are now filled. `pagedata_sweep.csv`.

## 6. Schema validation
Google Rich Results Test now requires sign-in (headless run blocked). Structural check of the new preview JSON-LD: Organization, SoftwareApplication, WebSite, WebPage(about=Thing), BreadcrumbList (positions 1–4, absolute items, all resolve), FAQPage (8 Question/Answer) — 0 errors; no `Product` without offers/review/rating anywhere. Commercial pages: Services keep `Service` schema (provider Organization), Pricing has no product schema; SoftwareApplication keeps `offers` (price 0). After deploy: GSC → Product snippets → Validate fix, then RRT on one guide.
Open question for owner: the global SoftwareApplication schema carries `aggregateRating 4.8 / 126`. If that figure is not from real collected ratings it must be removed (Google policy); not changed without approval.

## 7. User vs crawler parity (pharmaceuticals→germany, prod)
Browser (Playwright) vs Googlebot-UA HTML: identical h1, answer paragraph, snapshot values (HS 300490, 0 %, 0.7 %, $25.75B rank #3 of 225), same 8 FAQ questions, 15 related links, same 12 sections. Only differences: crawlers skip analytics/pixels and floating widgets.

## 8. AI-crawler access to the 975 sitemap URLs — `gptbot_all_urls.csv`, `ai_ua_matrix.csv`
GPTBot sweep: 975/975 HTTP 200. 413 answer docs: full text for every UA. 392 guides: 381 pre-rendered, 11 cached shells (same list). 170 other pages: 167 rendered; 3 shells (`/legal/terms`, `/academy/international-trade-basics`, `/services/buyer-discovery-service`) — same transient-render + sticky-cache pattern.
UA matrix (12 URLs): GPTBot, ChatGPT-User, OAI-SearchBot, PerplexityBot, Perplexity-User, ClaudeBot, Claude-User, bingbot (Copilot), Applebot all receive pre-rendered HTML. Bytespider, DuckAssistBot, Meta-ExternalAgent (and the non-crawler token Google-Extended) get the SPA shell on SPA routes — they can still read all 413 answer docs and `/llms.txt`. robots.txt allows all of them (fetched 200 by GPTBot; Cloudflare 403s generic `Python-urllib`).
Note: ChatGPT's browsing could not open the 92 KB JSON index; `/api/answers/index.html` (HTML) is added, pending deploy. `/llms.txt` is live now.

## Remaining issues
1. Deploy pending for items in §1.
2. 14 sticky edge-cached shells (11 guides + 3 pages) — app side fixed (no more cold holes); need edge cache expiry or a platform purge, then re-audit.
3. aggregateRating provenance (owner decision).
4. Minor-crawler shells on SPA routes (platform UA allow-list) — mitigated by answer docs + llms.txt.
