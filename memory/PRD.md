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
- [x] **Product Trade Profiles** `/products` + `/products/{slug}` — Basmati Rice, Agarbatti, Spices, Textiles, Pharmaceuticals (overview, HSN link, top importers/exporters, demand, opportunities, compliance, logistics, related corridors).
- [x] **Trade Corridor Pages** `/corridors` + `/corridors/{slug}` — India-to-UAE/USA/Australia/Armenia (export & import process, customs, duties, docs, opportunities, popular products, logistics).
- [x] **HSN Landing Pages** `/hsn/{code}` — 5 codes (10063020, 33074100, 09024020, 30049099, 62034299) with GST, RoDTEP, drawback, benefits, docs, customs notes, related products.
- [x] **Industries** `/industries` + `/industries/{slug}` — 8 sectors (Agriculture, Food Processing, Textiles, Chemicals, Pharma, Engineering, Handicrafts, FMCG).
- [x] **Blog / Knowledge Center** `/blog` + `/blog/{slug}` — 6 long-form posts across export guides, compliance, trade news, logistics, international marketing.
- [x] **Supplier Discovery** `/suppliers` — searchable directory with verified badges, q/country/category filters, locked-CTA for full database.
- [x] **Marketplace Preview** `/marketplace` — featured listings (6), trade reels (4), live buyer RFQs (3 with WhatsApp reply).
- [x] **Trade Network** `/network` — featured members (6) with avatars + stats (48K+ members, 92 countries).
- [x] **Mega-Nav** rebuilt: Home · Tools · AI Copilot · Explore▾ (Products/Corridors/Countries/Industries/Expos/Customs) · Platform▾ (Marketplace/Network/Suppliers/Intelligence) · Learn▾ (Academy/Blog/Trade News) · Contact.
- [x] **Sitemap.xml** expanded to 50+ URLs covering every new route.
- [x] All 60/60 backend API tests pass · all frontend flows verified across Phase 1 + 2 + 3 + 4.

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
