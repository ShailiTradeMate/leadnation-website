# LeadNation — ROADMAP (Volumes 2, 3, 4 + Backlog)

> Rule: Volume 1 is COMPLETE and must NOT be redesigned. Everything below EXTENDS the
> existing architecture. Reuse the existing LeadNation Brain (do NOT create another AI).
> Every new module belongs to a Trade Project, feeds the Reactive Computation Graph,
> integrates with the Brain, and flows into the downloadable PDF. No standalone modules.

## Owner
Vaibhav Deshmane · Vametra AI Technologies Pvt Ltd

---

## P1 BACKLOG (from user snip — near-term, independent of Volumes)
- [x] **Production polish sprint (2026-07-14)** — DONE & verified (iteration_27, 13/13). Global scroll-to-top fix, per-page SEO + JSON-LD builders + llms.txt, route lazy-loading, Instagram+LinkedIn via central `lib/brand.js`. See POLISH_SPRINT_REPORT_2026-07-14.md. Logos untouched (awaiting owner's final assets; tagline = "Intelligence Beyond Borders").
- [ ] **PRE-PUBLIC-LAUNCH SECURITY (mandatory):** Rotate `ADMIN_TOKEN` + `ADMIN_PASSWORD` to strong production values (Emergent Secrets tab → Redeploy). Kept unchanged for first deploy during web+app integration testing per owner. Update `/app/memory/test_credentials.md` when done.
- [ ] **Go-live payments:** Add LIVE Stripe secret key + Razorpay `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` (Secrets tab → Redeploy). Code is env-ready — Razorpay auto-activates for India, Stripe for international. Then live-test $105 (Stripe) + ₹10,000 (Razorpay) event-listing payments. (Owner sourcing keys.)
- [ ] **Razorpay wiring for India** — blocked on user API keys. Gateway toggle + pricing already in the Pricing Engine; just wire checkout/webhook when keys arrive.
- [ ] **My Reports history + shareable public/private links with expiry** — store generated reports per project; shareable link with visibility + TTL.
- [x] **Legal pages** — DONE (2026-07-05): Privacy, Terms, Cookie, Disclaimer, Refund at `/legal/*` (international scope, reusable links in footer/signup/checkout).
- [ ] **Activate Analytics scaffolding** — GA4 / GTM / Clarity / Meta Pixel via `.env` (scaffold already present in `components/Analytics.jsx`).
- [ ] **Web↔App deep linking (mobile phase)** — Android App Links + iOS Universal Links + Expo Linking anchored to website canonical URLs `/project/{id}` & `/report/{id}`. Do NOT use Firebase Dynamic Links (deprecated). Website v1.0 does not implement these routes yet — documented in APP_BUILD_PROMPT.md + integration guide §13.

---

## VOLUME 2 — TRADE SIMULATION & DECISION ENGINE  (foundational, HIGH priority)
Each Trade Project becomes a Digital Twin; everything recalculates instantly.
- **Phase 2A — DONE (2026-07-05)** — Digital Twin, Scenario Builder (+compare/merge/duplicate/archive/versioning), Trade Score Engine (8 explainable scores), Decision Engine layer, Universal Audit Trail (events), Live Data Adapter framework, Brain recommendations, Volume-2 PDF integration (scores/scenarios/decision/Report ID/QR). Verified iteration_24 (19/19 backend).
- **Phase 2B — Monte Carlo Simulation + Sensitivity Analysis**
  - Monte Carlo: FX, freight, duty, delay, commodity price, demand, volatility → Best/Expected/Worst + probability + confidence.
  - Sensitivity: most sensitive variable, highest cost/risk/profit impact; Brain explains.
- **Phase 2C — Trade Recommendation Engine + Risk Simulation + Trade Forecast**
  - Recommendations: better Incoterm/currency/route/mode/pricing/timing/buyer/supplier (Brain, continuous).
  - Risk Simulation: political, currency, weather, compliance, supplier, buyer, port congestion, geopolitical, sanctions, disaster, container, banking, insurance.
  - Forecast: 30/90/180/365-day market/profit/demand/risk (Brain).
- **Phase 2D — Interactive World Map + PDF integration for Volume 2**
  - Heatmaps: routes, risk, demand, growth, opportunities.
  - PDF: simulation results, scenario comparison, twin, risk, recommendations, forecast, sensitivity, exec summary, charts.

## VOLUME 3 — GLOBAL TRADE INTELLIGENCE NETWORK
- **3A** Live Data Adapters: commodity, FX, freight, shipping, weather, ports, customs, govt, banking, insurance, trade agreements, import/export restrictions.
- **3B** Buyer Intelligence + Supplier Intelligence.
- **3C** Market Intelligence + Country Intelligence (195 countries).
- **3D** Compliance Intelligence (country×product) — docs, licenses, inspection, testing, certificates, permits.
- **3E** **Packaging Intelligence (mandatory)** — country/product packaging checklist, primary/secondary/export packaging, palletization, container loading/type, wood treatment, fumigation, DG, hazard labels, UN markings, barcodes/QR, labelling rules, shelf life, temp/humidity, weight/stacking limits, packaging cost + time, Brain recommendations, downloadable checklist.
- **3F** Documentation Intelligence (country/product specific doc set).
- **3G** Trade News (Brain-summarized global/product/country impact — extends existing).
- **3H** PDF integration for Volume 3.

## VOLUME 4 — ENTERPRISE TRADE OS
- CRM (customers/suppliers/leads/partners), ERP-ready (inventory/warehouse/purchase/sales/mfg),
  Workflow Engine (tasks/approvals/assignments/notifications), Team Collaboration (comments/mentions/approvals/version history),
  Document Management (OCR/AI search/classification), Executive Dashboard (company+trade KPIs/revenue/profit/forecast),
  Enterprise APIs (ERP/SAP/Oracle/Microsoft/Tally/Zoho/QuickBooks), White Label (branding/reports/PDF/portal),
  Enterprise Security (RBAC/audit/logs/encryption/SSO).
- PDF integration for Volume 4.

## UNIVERSAL PDF ENGINE (cross-cutting)
Professional trade-intelligence report: cover page, branding, project summary, exec summary, full
Incoterm costing (EXW/FOB/FCA/FAS/CFR/CIF/CIP/DAP/DPU/DDP), landed cost, taxes/duties/FX/insurance/freight,
simulation, scenario comparison, risk, trade health, compliance, packaging checklist, documentation checklist,
buyer/supplier/country intelligence, trade news, Brain analysis, recommendations, next steps, charts/graphs,
appendix, disclaimers, Report ID, QR code, generation date, page numbers.

## Deliverables per volume
Updated blueprint · architecture diagrams · DB design · API contracts · Brain integration · PDF integration · test report · completion checklist.


---

## MARKETING / VISIBILITY — TOP PRIORITY (2026-06)
Goal: discoverable worldwide (India + 195 countries) via SEO + GEO + social.

### Readiness snapshot (audited on production)
STRONG & LIVE: robots.txt, sitemap.xml (77 URLs), per-route meta via react-helmet (verified served to Bingbot WITHOUT JS on prod), JSON-LD (Organization, SoftwareApplication, WebSite+SearchAction), OG/Twitter cards + og-default.png, llms.txt (GEO/AI), PWA manifest, PostHog, Analytics.jsx scaffold (GA4/GTM/Clarity/Meta Pixel via .env), programmatic pages (countries/products/corridors/HSN/tools).
GAPS: (1) NOT registered with Google Search Console / Bing Webmaster Tools (user confirmed) — engines don't know the site exists = #1 reason for zero visibility. (2) New domain, zero backlinks/authority. (3) Body is client-rendered (meta fine; full-body prerender would boost Bing/AI). (4) No IndexNow. (5) No FAQ/Breadcrumb schema. (6) Social cadence not set. (7) GA4 id not yet in .env.

### Phased plan
- P0 USER (this week): create+verify Google Search Console & Bing Webmaster Tools (I can host the verification file if given the token), submit sitemap.xml, "Request indexing" on top 10 pages, create GA4 property + send me the Measurement ID.
- P0 AGENT (code): IndexNow key file + auto-ping on content change; FAQPage + BreadcrumbList schema on key pages; sitemap lastmod; ensure Analytics.jsx wired once GA4 id provided.
- P1 AGENT (code): react-snap full-body prerender of the 77 URLs (biggest Bing + AI-crawler win); expand programmatic pages (more countries/products/corridors/HSN); blog/academy long-tail content engine; auto-regenerate sitemap from data.
- P1 USER: backlinks (trade directories, EPCs/FIEO, Product Hunt, G2/Capterra, Crunchbase), LinkedIn + Instagram posting cadence (accounts already in schema sameAs), PR/outreach.
- P2: hreflang/localization for priority markets, AggregateRating/Review schema, WhatsApp share buttons, newsletter/email capture, YouTube/short-form.

## Product backlog (2026-06)
- [ ] Reveal Limits (per-plan monthly cap; `buyer_contact_reveals` logging ready)
- [ ] My Revealed Buyers (saved list per subscriber)
- [ ] Redeploy Safeguard (verify-before-delete prune hardening → prod)
- [ ] Weekly Buyer Digest (Resend)
- [ ] Save to CRM / vCard export on reveal card
- [ ] VBIE France SIRENE / Japan NTA / Australia ABN — flip on when user provides keys (after marketing)
