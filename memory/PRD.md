# LeadNation — Global Trade Intelligence Portal

## Problem Statement (verbatim)
Build a premium 3D website for the LeadNation app to drive organic traffic, account registrations and app downloads. Tabs: Home (3D animated globe, moving pictures/videos, search bar), Customs & Compliance, Trade News, Contact Us (with map + Instagram), Expo, Product Info. Floating WhatsApp on all pages. India-focused features. Every page has Download App + Create Account CTAs. References: Apple, Jacob & Co, Tesla, Stripe, OpenAI. Color palette: #0A2540 / #00C2FF / #7C3AED / #050816. Hosting: DigitalOcean (deployment-ready). Engines are mocked Phase-1; API-ready for real backend later.

## Architecture
- **Frontend**: React 19 + react-router 7, react-globe.gl (Three.js), framer-motion (available), Tailwind CSS, @phosphor-icons/react, topojson-client (country outlines on globe). Dark cinematic theme (Manrope display + IBM Plex Sans + JetBrains Mono).
- **Backend**: FastAPI + Motor (MongoDB). All endpoints under `/api/*`. Engines (`/customs-compliance`, `/trade-news`, `/expos`, `/product-info`, `/india-features`, `/search`) return curated mock data — replace with real engine calls later.
- **Storage**: MongoDB (`leads` collection persists contact submissions).
- **Routing**: `/`, `/customs-compliance`, `/product-info`, `/expo`, `/trade-news`, `/contact`.

## User Personas
- **Indian SME exporters** — need GST, DGFT, RoDTEP, FTA help.
- **Global importers & wholesalers** — need country-specific duty + cert info.
- **Investors & partners** — need an investor-grade landing experience.

## Core Requirements (static)
1. 3D animated globe with arcs from Indian cities to global trade hubs.
2. Search bar (products + countries).
3. Six dedicated tabs.
4. Floating WhatsApp button (number +91 82371 61088).
5. Every page CTAs: Download App (Coming Soon · App Store + Play Store) + Create Account.
6. Contact page with email/whatsapp/Instagram/address + embedded OpenStreetMap.
7. India-first features section.

## Implemented (2026-06)
**Phase 7 — LeadNation Brain & Intelligence Layer** (Jun 2026)
- [x] **Backend refactor**: monolithic `server.py` (1.7k lines) split into thin entrypoint + domain modules — `core.py`, `reference.py`, `engines.py`, `search.py`, `leads.py`, `trade_tools.py`, `ai.py`, `content.py`, `services.py`, `admin.py`, `analytics.py`. ZERO regressions (38/38 backend tests pass).
- [x] **`brain/` package** — the central reusable intelligence layer (shared by website, app, future portals):
  - `knowledge.py` — `knowledge_base` collection as Single Source of Truth (SSOT); auto-seeds ~61 entries from countries/products/HSN/corridors/industries/services/blog/academy + curated compliance & schemes. `kb_search` / `kb_get` / `kb_stats`.
  - `engines.py` — 12 engines: country_context, trade_news, market_intelligence, learning, compliance, tariff, logistics, policy, product_intelligence, business_services, marketplace, network.
  - `router.py` — `orchestrate()`: intent detection + entity extraction (country/product/HSN/service) + engine selection + multi-engine composition. Logs `brain_queries` + `brain_usage` for analytics.
  - `providers.py` — configurable AI provider (env `BRAIN_AI_PROVIDER`, default `mock`; supports openai/anthropic/gemini/local). Live calls DEFERRED — deterministic engine composition for now.
  - `memory.py` — `conversation_memory`, `user_context`, `saved_preferences` (preferred country/products/industries, role, recent searches, saved items).
  - `search_layer.py` — Universal Search with 5-tier priority (KB → DB → Engines → External APIs [disabled] → Public Web [disabled, no scraping]).
  - `context.py` — retrieval/context builder seam for future live AI.
- [x] **Brain API**: `/api/brain/ask`, `/search`, `/engines`, `/status`, `/context/{uid}`, `/conversation/{sid}`, `/save`, `/knowledge`.
- [x] **Admin Brain API**: `/api/admin/brain/overview` (engine health, KB status, AI usage, most-asked, top countries/products/HSN/services, trending, failed queries, knowledge gaps), `/knowledge`, `/knowledge/reseed`.
- [x] **Frontend**: flagship `/brain` page (multi-engine unified answers, engine pills, source cards, session memory, suggested prompts); `/ai-assistant` → redirects to `/brain`; nav "AI Copilot" → "LeadNation Brain"; admin `/admin/brain` dashboard + Brain tab in CMS.
- [x] **Tested**: testing_agent iteration_5 — 100% backend + frontend, zero issues.

## Implemented (2026-01)
**Phase 1 — Core portal**
- [x] Cinematic dark UI, Manrope + IBM Plex font pairing, custom logo, gradient text.
- [x] Animated 3D globe with country outlines + 10 trade-route arcs + 12 hub points.
- [x] Home: hero, search w/ live autocomplete, suggestion chips, stats, marquee, feature bento (6), India features (6 dynamic), Apple-style image storytelling, download CTA.
- [x] Customs & Compliance: country selector, Import/Export toggle, duty/documents/incoterms/tip — auto-refresh on change.
- [x] Trade News: hero featured article + masonry-style grid of 5 more.
- [x] Expo: category filter chips, 8 expo cards w/ image, date, city, attendees.
- [x] Product Info: 4-select form, auto-initial result, market size/buyers/suppliers/certs/incoterms/insights.
- [x] Contact: lead form (persists to Mongo), contact rows, embedded OSM map at Ahilyanagar coords, Instagram link.
- [x] Floating WhatsApp button on every page.
- [x] Production-ready App Store / Play Store CTA badges (Coming Soon).
- [x] Footer with all contact + nav + download badges.
- [x] data-testid attributes throughout for QA.

**Phase 2 — SEO Growth Engine** (Jan 2026)
- [x] **Customs Duty Calculator** `/tools/duty-calculator` — country, category, value, currency → duty, VAT, handling, landed cost. FTA detection per corridor.
- [x] **Country Profile Pages** `/countries/{slug}` for India, UAE, USA, Australia, Armenia + index at `/countries`. Each has overview, imports, exports, opportunities, customs, compliance, news, events, marketplaces. Built to scale to 250+ countries.
- [x] **Learning Academy** `/academy` — Beginner / Intermediate / Advanced. 9 premium course cards with topics on import/export process, documentation, customs clearance, FTA arbitrage, supply chain finance, global compliance.
- [x] **Trade Intelligence Hub** `/intelligence` — gold, silver, oil (Brent + WTI), copper, natural gas + 8 currency pairs + 6 global market trends.
- [x] **SEO Infrastructure** — sitemap.xml, robots.txt, react-helmet-async dynamic meta (title + description + keywords + canonical), Open Graph + Twitter cards, JSON-LD structured schema (Organization, WebApplication, Country, EducationalOrganization) on each page.
- [x] **Nav Tools dropdown** + Footer expanded with new tool links.

**Phase 3 + 4 — Trade Intelligence Ecosystem** (Jan 2026)
- [x] **Trade Tools Hub** `/tools` + 7 individual tools: HSN Finder, Duty Calculator, Landed Cost Calculator, Export Incentive Finder, Product Research, Buyer Discovery, Export Readiness Score (3-step funnel with lead capture).
- [x] **AI Trade Copilot** `/ai-assistant` — chat UI with suggested prompts; mocked-but-realistic responses with `MOCKED RESPONSE — LIVE AI COMING SOON` badge; suggested-tools links per answer. Ready for GPT integration.
- [x] **Product Trade Profiles** `/products` + `/products/{slug}` — Basmati Rice, Agarbatti, Spices, Textiles, Pharmaceuticals.
- [x] **Trade Corridor Pages** `/corridors` + `/corridors/{slug}` — India-to-UAE/USA/Australia/Armenia.
- [x] **HSN Landing Pages** `/hsn/{code}` — 5 codes with GST, RoDTEP, drawback, benefits, docs, customs notes, related products.
- [x] **Industries** `/industries` + `/industries/{slug}` — 8 sectors.
- [x] **Blog / Knowledge Center** `/blog` + `/blog/{slug}` — 6 long-form posts.
- [x] **Supplier Discovery** `/suppliers`, **Marketplace** `/marketplace`, **Network** `/network`.
- [x] **Mega-Nav** rebuilt: Home · Tools · AI Copilot · Explore▾ · Platform▾ · Learn▾ · Contact.

**Phase 5 — Revenue Engine, Admin CMS & Business Scale** (Jan 2026)
- [x] **Analytics architecture**: env-driven loaders for GA4 / GTM / Microsoft Clarity / Meta Pixel + first-party event tracking via `/api/track` + `trackEvent()` wired into Create-Account, Download-App, WhatsApp, Contact form, Service Request submissions, page views.
- [x] **Admin CMS** `/admin-login` → `/admin-cms` (token-gated, default `leadnation-admin-2026`): Dashboard (8 stat cards), Content (6 collections with create/edit/delete via JSON editor — countries, products, corridors, hsn_codes, industries, blog), Leads tab (search + CSV export at `/api/admin/leads.csv`), Service Requests tab (status dropdown + CA assignment input), Events tab (page views + custom events).
- [x] **MongoDB content migration**: all 6 collections auto-seeded on startup if empty; CMS reads/writes go to MongoDB; no more hardcoded reads for those collections.
- [x] **Business Services** `/services` + `/services/{slug}` — 10 services (RCMC, GST, IEC, Company Registration + 6 consulting: Export, Import, Compliance, Market Entry, Product Sourcing, Buyer Discovery Service). FAQ accordion + lead form → creates `service_request` + `lead` (linked CA workflow: new → assigned → in-progress → completed/cancelled).
- [x] **Directory** `/directory` + `/directory/{kind}` — exporters, importers, suppliers, CHA, export-agents with search + country filter + locked-CTA.
- [x] **Global Search** `/search` — searches products, countries, corridors, industries, blogs, HSN, services, tools with typed result badges.
- [x] **Sitemap.xml** expanded to ~70 URLs (services + directories + everything from Phase 1–4).
- [x] All admin endpoints token-gated via `X-Admin-Token` header (query token for CSV downloads only).
- [x] **Testing**: 29/30 backend pytest pass · all frontend flows verified · 2 bugs caught and fixed (Home Globe regression + global-search type singularisation).

## Backlog / Next
- **P0** Connect real engines (customs, trade news, expo, product info, search) once API docs are shared by user.
- **P0** Replace coming-soon URLs with live App Store + Play Store URLs.
- **P0** Add real logo + brand assets when ready.
- **P1** Add Hindi + regional language toggle (string already mentioned in India features).
- **P1** Add Trade Intelligence Engine + Learning Academy Engine endpoints.
- **P1** Add video hero (port cranes / trade montage) instead of static images for moving-pictures section.
- **P1** Email/transactional integration (SendGrid/Resend) so leads also email the team.
- **P1** Sitemap / SEO meta tags / OG images (critical for organic-traffic goal).
- **P2** Pydantic model for `product-info` request; tighten CORS.
- **P2** Cap `/search` empty-q response.
- **P2** Replace OpenStreetMap iframe with Mapbox / Google Maps when API key provided.
- **P2** PWA / install banner on web.

## Deployment Notes
- Build with `yarn build` (CRA) and host static `build/` on DigitalOcean App Platform / nginx.
- Backend runs as ASGI (uvicorn server:app) — Docker-friendly. MongoDB via `MONGO_URL`.
- Update `REACT_APP_BACKEND_URL` to production domain when deploying.
