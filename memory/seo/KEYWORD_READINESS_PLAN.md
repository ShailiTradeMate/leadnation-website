# Vametra AI — Keyword → Page Readiness Plan
Built 7 Oct 2026 from `Vametra_Master_SEO_GSC_Bing_Keyword_Map.xlsx` (2,149 keywords) + `/app/memory/SEO_KEYWORDS.md`.

---
## 0. What the audit of the Excel found

| Finding | Detail | Action |
|---|---|---|
| ✅ Every target URL in the sheet maps to a real route | 47 static + 12 dynamic routes checked against `App.js` | none |
| ⚠️ **753 keywords dumped on `/ai-assistant`** | Only 32 are genuinely AI-intent. **721 are Product × Country** long-tail ("basmati rice duty in uae", "agarbatti buyers in qatar") | Remap — see §1 |
| ⚠️ Dynamic slugs render for ANY value | `/countries/china`, `/corridors/india-to-uk` resolve but have no data → thin/soft-404 pages Google will drop | Build data first, then link |
| ⚠️ 50 noise terms in the library | "india mart", "e support kvs ro bhopal" etc. | Already in Excluded Noise — keep out of regex & content |
| ✅ Regex packs rebuilt | 14 themed + 4 combined, all <4,096 chars, 100% library coverage | `GSC_REGEX_PACKS.md` |

---
## 1. The single biggest win: Product × Country pages (P0)

721 keywords in the sheet follow exactly 8 intent patterns per product-country pair:

1. `{product} duty in {country}` 2. `{product} customs duty in {country}` 3. `{product} hs code for {country}`
4. `{product} buyers in {country}` 5. `{product} importers in {country}` 6. `export {product} to {country}`
7. `{product} demand in {country}` 8. `{product} export documents for {country}`

**One page answers all eight.** Proposed route: `/export/{product}/to/{country}`
(e.g. `/export/basmati-rice/to/uae`) — keeps `/products/:slug` as the product hub and
`/countries/:slug` as the country hub, with the new route as the money page.

Launch matrix = 10 products × 10 countries = **100 pages** covering ~800 keywords:
- Products: basmati-rice, agarbatti, spices, textiles, pharmaceuticals, tea, leather, handicrafts, engineering-goods, organic-food
- Countries: uae, usa, uk, saudi-arabia, australia, singapore, germany, netherlands, qatar, armenia

Required page skeleton (this is the template I would build):
```
H1            Export {Product} from India to {Country} — Duty, HS Code & Buyers
Answer block  40-60 words: HS code, duty %, FTA status, as-of date      ← what AI engines quote
Data table    HS code · basic duty · preferential/FTA duty · VAT/GST · as-of date · source
Section       Documents required (checklist)
Section       Who buys it in {Country} (buyer count + sample verified-buyer teaser → /buyers)
Section       Landed cost worked example (CIF, 1 FCL) → /tools/landed-cost-calculator
Section       Demand & trend (2-3 real figures with year)
FAQ           The 8 intents above as 8 Q&As  → FAQPage schema
Internal      → /products/{product}, /countries/{country}, /corridors/india-to-{country},
                /tools/duty-calculator, /tools/hsn-finder
Schema        FAQPage + BreadcrumbList + Dataset
```

---
## 2. Per-page readiness checklist (apply to all 47 existing pages)

For each page, in this order:
1. **One primary keyword** from the sheet (never two pages on the same term).
2. **Title tag** ≤60 chars: `Primary Keyword — Benefit | Vametra AI`
3. **Meta description** ≤155 chars, answers the query, contains a number or a date.
4. **H1** contains the primary keyword verbatim.
5. **Answer-first opening** — 40-60 words directly answering the query, before any marketing copy.
6. **One dated, citable data block** (table) with an "as of <month year>" line + source name.
7. **2-4 H2s** using the secondary keywords from the same category in the sheet.
8. **FAQ block** of 4-8 real questions from the sheet's question-intent rows → `FAQPage` schema.
9. **Internal links**: 3 outbound to related money pages, 1 to a tool, 1 to a country/corridor.
10. **data-testid + alt text** on every image, descriptive filenames.
11. Page added to the dynamic sitemap (automatic) and IndexNow auto-ping (automatic).

### Page → primary keyword assignment (from the sheet, deduped)
| Page | Primary keyword | Secondary cluster |
|---|---|---|
| `/` | trade intelligence platform | global trade data, import export platform |
| `/tools/duty-calculator` | custom duty calculator india | import duty calculator, customs duty by hs code |
| `/tools/hsn-finder` | hs code finder | hsn code search for export, itc-hs lookup |
| `/tools/landed-cost-calculator` | landed cost calculator | cif vs fob, incoterms cost, freight calculator |
| `/tools/export-incentive-finder` | export incentive calculator india | rodtep rate finder, duty drawback, epcg |
| `/tools/find-buyers` | how to find buyers for export from india | buyer finder, export leads, importer search |
| `/tools/product-research` | export product research | products in demand for export, profitable export products |
| `/tools/export-readiness` | export readiness assessment | first time exporter, export business requirements |
| `/buyers` | verified importers list | buyer verification, buyer trust score, sanctions screening |
| `/brain` | ai for export import business | ai trade assistant, chatgpt for exporters |
| `/intelligence` | trade intelligence | customs data, shipment records, global trade data |
| `/expo` | trade fairs and exhibitions | gulfood, canton fair, b2b matchmaking |
| `/trade-news` | global trade news | tariff news, trade policy updates, freight trends |
| `/customs-compliance` | customs compliance for exporters | trade compliance, rules of origin, cbam |
| `/academy` | learn export import business | international trade course, exim training |
| `/services/iec-registration` | iec code registration process | dgft, importer exporter code, iec certificate |
| `/services/rcmc-registration` | rcmc certificate apply online | export promotion council, registration cum membership |
| `/services/gst-registration` | gst for exporters | lut for export, gst refund on exports |
| `/services/export-consulting` | export consultant india | export consultancy, market entry consultant |
| `/services/product-sourcing` | supplier sourcing service | international sourcing, manufacturer database |
| `/pricing` | best export import software india | import export software, trade platform pricing |
| `/countries/{c}` | {country} trade profile | {country} tariff, {country} buyers, {country} imports |
| `/corridors/india-to-{c}` | export from india to {country} duty | india {country} fta, india {country} shipping |
| `/products/{p}` | {product} export hs code and duty | {product} buyers, {product} export documents |
| `/export/{p}/to/{c}` | {product} duty in {country} | the 8 intents in §1 |

---
## 3. Build order (what I execute, in sequence)

**Phase 1 — foundations (no new pages)**
- Answer-first block + dated data table + FAQ schema on the 13 money pages above.
- Title/meta/H1 rewrite from the table in §2.
- Fix the `/ai-assistant` mapping: keep the 32 AI keywords, remap the other 721.

**Phase 2 — country & corridor data (unlocks real pages)**
- Add data for China, UK, Netherlands, Germany, Singapore, Saudi Arabia, Bangladesh, Qatar.
- 8 new corridor pages + 8 new country profiles, each with FY25-26 trade values and duty tables.

**Phase 3 — the programmatic engine**
- `/export/{product}/to/{country}` route + template + 100-page launch matrix.
- Auto-add to sitemap (already automatic) → IndexNow auto-ping fires on publish (already automatic).

**Phase 4 — measurement**
- GSC: save the 4 combined regex packs as filters; track clicks/impressions per theme weekly.
- Bing: work the 236-seed list through Keyword Research, 10 URL submissions/day.
- GA4: `AI Engine` custom dimension + `AI Answer Engines` channel group (already instrumented).
- Monthly GEO prompt audit (10 prompts in `SEO_KEYWORDS.md` §C).

---
## 4. How to add the keywords to GSC & Bing (step by step)

**Google Search Console**
1. Performance → Search results → **+ New** → **Query**
2. Tab **Custom (regex)** → dropdown **Matches regex**
3. Paste **Combined Pack 1** from `GSC_REGEX_PACKS.md` → Apply → bookmark the URL
4. Repeat for Packs 2-4. For theme reporting, repeat with the 14 themed packs instead.
5. GSC has no "target keyword list" — regex filters + bookmarks *are* the tracking mechanism.
6. Optional: Settings → Associations → link GA4, then build the same filters in Looker Studio
   (the packs are RE2-safe, so they work there and in the BigQuery bulk export too).

**Bing Webmaster Tools**
1. Bing has **no regex filter**. Use the **Bing Seed List** sheet (236 seeds) instead.
2. Keyword Research → paste 10-20 seeds at a time → export → keep anything with impressions.
3. URL Submission → submit up to 10 priority URLs/day (IndexNow already pushes all 85+ automatically).
4. Performance → filter by query manually for the top 20 terms; log weekly in the Excel.
5. AI Performance (New) → this is the Copilot/GEO scoreboard — check monthly.

**Keeping the library alive**
- Add new keywords to the Excel `SEO Keyword Library` sheet (same columns).
- Re-run `python3 /app/memory/seo/gsc_regex_packs.py` → it reports any keyword the packs miss.
- Never target the same keyword from two pages; the sheet's `Target / Current URL` column is the source of truth.
