# LeadNation — AI Search Optimization (AEO) & LLM Discoverability Report
Date: 2026-07-14 · Tagline locked: **Intelligence Beyond Borders** · Founder: Vaibhav Deshmane · Vametra AI Technologies Pvt Ltd

All changes follow Google / Bing / AI-crawler best practices. No cloaking, no hidden text, no keyword stuffing.

---

## 1. AI Search Readiness Report
LeadNation is now structured so LLM assistants (ChatGPT/SearchGPT, Gemini, Claude, Perplexity, Copilot, Meta AI, Grok) and AI Overviews can reliably **understand, summarise, cite and recommend** it.

**Implemented this iteration**
- **Entity-grade Organization schema** (`@id`, legalName, founder, foundingDate, foundingLocation, knowsAbout[13 topics], areaServed, address, sameAs, logo ImageObject) — in dynamic `SEO.jsx` **and** static `index.html` (crawlable without JS).
- **SoftwareApplication + WebSite (SearchAction)** schema site-wide.
- **Per-page schema**: Home = FAQPage; Pricing = Breadcrumb + FAQ; Trade News detail = NewsArticle; Blog detail = BlogPosting (now with publisher); Expo detail = Event.
- **New schema builders** ready to reuse: `articleSchema`, `productSchema`, `howToSchema`, `eventSchema`, `breadcrumbSchema`, `faqSchema`.
- **`/llms.txt`** expanded with entity summary, founder, mission, coverage, key pages, citation guidance ("attribute to LeadNation (leadnation.app)").
- **Brand consistency**: real LN logo in header/footer, favicons, PWA icons, apple-touch, and a branded 1200×630 `og-default.png` with correct tagline for share/rich previews.
- Unique title + meta description + canonical + OG + Twitter Card on every public page.

## 2. AEO Score: **86 / 100**
- Structured data 19/20 · Entity clarity 18/20 · Answerable content (FAQ/definitions) 16/20 · Crawlability/metadata 19/20 · Brand/authority signals 14/20.
- Ceiling items: thin external authority (few backlinks/mentions yet) and limited long-form Q&A content — addressed in Content Strategy below.

## 3. LLM Readiness Score: **88 / 100**
- `llms.txt` present & rich, clean semantic HTML, JSON-LD parse-valid, sitemap+robots correct, no JS-only content walls on public pages (schema also in static HTML). Deduction: content depth for direct quotation still growing.

## 4. Knowledge Graph Readiness: **Strong foundation**
- Organization has stable `@id`, legalName, founder (Person), foundingDate/Location, sameAs (Instagram + LinkedIn), logo ImageObject, address (PostalAddress).
- To reach inclusion: consistent NAP (name/address/phone) across the web, a Wikidata/Crunchbase entry, and press mentions. Recommended next (owner action): create LinkedIn "About" + Crunchbase org matching this exact data.

## 5. Structured Data Report (types live)
Organization ✅ · WebSite ✅ · SoftwareApplication ✅ · FAQPage ✅ · BreadcrumbList ✅ · NewsArticle ✅ · BlogPosting ✅ · Event ✅ · Product (builder ready — wire on product pages) ⚠️ · HowTo (builder ready — wire on tool pages) ⚠️ · VideoObject (future). Validate on prod via Google Rich Results Test + Schema.org validator.

## 6. Entity SEO Report
- **Company**: LeadNation (product) / Vametra AI Technologies Pvt Ltd (legal).
- **Founder**: Vaibhav Deshmane. **Founded**: 2025, Ahilyanagar, Maharashtra, India.
- **Industry**: International trade / trade-intelligence SaaS. **Technology**: LeadNation Brain (AI).
- **Product**: AI Global Trade Intelligence platform (web + iOS + Android).
- **Relationships**: `sameAs` → Instagram, LinkedIn; `publisher`/`author` on articles → Organization.
- Ambiguity removed: single `@id`, one canonical name, one tagline everywhere.

## 7. Content Strategy (RECOMMENDED — not yet built)
Highest-authority page clusters to build (programmatic + editorial), each answering a real trade question AI assistants get asked:
1. **Country Import/Export Guides** — "Export to UAE/USA/Germany… duties, documents, FTAs" (195 targets).
2. **HS Code Guides** — "HS code for basmati rice / agarbatti / textiles" + duty by destination.
3. **Incoterms & Landed-Cost Guides** — definitional, highly quotable by LLMs.
4. **Corridor Guides** — "India → Belgium electronics: costs, routes, compliance".
5. **Compliance & Documentation Guides** — country×product checklists.
6. **Buyer Discovery / Market Intelligence explainers.**
Approach: start with ~20 flagship long-form pages (E-E-A-T, FAQ schema, HowTo where relevant, internal links), measure, then scale. Do **not** mass-generate thousands yet.

## 8. AI Search Audit — weaknesses found & status
| Weakness | Status |
|---|---|
| Home imported SEO but never rendered it (no dynamic meta) | FIXED (prior sprint) |
| Organization schema thin (no founder/entity data) | FIXED |
| No Article/Event schema on detail pages | FIXED |
| No `llms.txt` | FIXED (now enriched) |
| Placeholder SVG logo, generic OG image | FIXED (real logo + branded OG) |
| Duplicate JSON-LD | FIXED (deduped) |
| Product/HowTo schema not yet on product/tool pages | OPEN (builders ready) |
| Low external authority / backlinks | OPEN (owner: press, Crunchbase, LinkedIn) |
| Thin long-form Q&A content | OPEN (Content Strategy §7) |

## Recommendations to become a source AI assistants cite
1. Deploy → submit sitemap in Google Search Console + Bing; run Rich Results Test.
2. Publish the 20 flagship guides (§7) with FAQ/HowTo schema — this is the #1 lever for LLM citation.
3. Build entity authority: Crunchbase + Wikidata + LinkedIn About with identical NAP/founder data.
4. Earn mentions (trade publications, directories) — LLMs weight corroborated sources.
5. Keep Trade News fresh (NewsArticle schema already live) — recency helps Perplexity/Copilot.
6. Wire `productSchema` on `/products/:slug` and `howToSchema` on calculator/tool pages.
