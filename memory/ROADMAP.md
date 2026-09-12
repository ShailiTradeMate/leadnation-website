# Vametra AI / LeadNation — MASTER BACKLOG & ROADMAP
_Last consolidated: 2026-06 (pre-deployment freeze, owner moving to Marketing / SEO / GEO)_

> Rule: Volume 1 is COMPLETE and must NOT be redesigned. Everything below EXTENDS the
> existing architecture. Reuse the existing LeadNation Brain (do NOT create another AI).
> Identity rule (frozen): DigitalOcean shared service owns buyer identity, Customer ID, GEID,
> profile and Firebase bridge. The website never creates a competing identity/onboarding system.
> Shared verification status values are `approved` / `rejected` (NOT `verified`).
> Member↔company linking must be confirmed via the DO authoritative readback API, never by
> reading local `members_bridge` Mongo in preview.

## Owner
Vaibhav Deshmane · Vametra AI Technologies Pvt Ltd

---

# 0. ACTIVE PHASE (owner decision) — MARKETING / SEO / GEO
Build is being deployed as-is. All engineering items below are parked until marketing is underway.

## 0.1 P0 — OWNER ACTIONS (cannot be done by agent)
- [ ] Create + verify **Google Search Console** and **Bing Webmaster Tools** (agent can host the verification file if given the token) — biggest single cause of zero visibility today.
- [ ] Submit `sitemap.xml` (77 URLs) in both; "Request indexing" on top 10 pages.
- [ ] Backlinks: trade directories, EPCs/FIEO, Product Hunt, G2/Capterra, Crunchbase.
- [ ] LinkedIn + Instagram posting cadence (accounts already in JSON-LD `sameAs`).
- [ ] PR / outreach for domain authority (new domain, zero backlinks today).

## 0.2 P0 — AGENT CODE WORK (SEO/GEO)
- [ ] **IndexNow**: key file + auto-ping on content change.
- [ ] **FAQPage + BreadcrumbList schema** on key pages.
- [ ] **sitemap `lastmod`** + auto-regenerate sitemap from data.
- [ ] Confirm GA4/GTM/Clarity env vars are present in the **deployment** env (already wired in code, `REACT_APP_GA4_ID` / `REACT_APP_GTM_ID` / `REACT_APP_CLARITY_ID`, consent-gated). If Realtime shows no data after deploy → the 3 vars are missing in deploy settings.

## 0.3 P1 — SEO/GEO depth
- [ ] **react-snap full-body prerender** of the 77 URLs — biggest Bing + AI-crawler win (body is currently client-rendered; meta is already served without JS).
- [ ] Expand programmatic pages (more countries / products / corridors / HSN).
- [ ] Blog / academy long-tail content engine.
- [ ] GEO: keep `llms.txt` in sync with new content; add per-page AI-answer summaries.

## 0.4 P2 — SEO/GEO
- [ ] hreflang / localization for priority markets.
- [ ] AggregateRating / Review schema.
- [ ] WhatsApp share buttons, newsletter/email capture.
- [ ] YouTube / short-form video presence.

### SEO readiness snapshot (audited on production)
LIVE & STRONG: robots.txt, sitemap.xml (77 URLs), per-route meta via react-helmet (verified served to Bingbot without JS), JSON-LD (Organization, SoftwareApplication, WebSite+SearchAction), OG/Twitter cards + og-default.png, llms.txt, PWA manifest, PostHog, GA4 `G-H5809GHQXW`, GTM `GTM-5JM23MH4`, Clarity `y2xx93q69j`, programmatic pages.
GAPS: not registered with GSC/Bing, no backlinks, client-rendered body, no IndexNow, no FAQ/Breadcrumb schema, social cadence not set.

---

# 1. P0 — POST-DEPLOY VALIDATION OF THE LAST FEATURE BATCH
The bulk-approval / subscription-request / verified-buyer-sync / registry-onboarding batch is
**implemented and agent-tested at API level, but NOT user-confirmed end-to-end.** Validate before
building anything new on top of it.

- [ ] **Main-admin approval inbox in the browser**: correct main-admin mode renders, bulk-approve control visible, all pending request types listed (review recommendations, profile/demographic edits, free-month grants, delete requests), per-item success/failure reported, no stale sub-admin token influencing role.
- [ ] **One controlled end-to-end fixture run**: sub-admin reject recommendation → profile change request → free-month request → main-admin bulk approve → DO canonical status readback (`approved`) → buyer appears in both Verified Buyer areas + Command Center Verified Buyers + Admin CMS Verified Buyer list → cleanup by hard delete. Use fresh fixtures; never reuse a deleted one.
- [ ] **CMS buyer list latency**: re-check `/api/buyers/admin/list` in the browser (was ~13s curl / >30s browser before batching fix). Confirm no duplicate frontend calls.
- [ ] **Sanitize `admin_approval_requests`**: backfill/repair malformed historical rows (missing payload) — defensive guards exist, data is still dirty.
- [ ] **Hard-delete consistency**: no local orphan submissions/records when the canonical DO user is gone; associated approval requests auto-cancelled.
- [ ] **Terminology**: local workflow still reports `status: verified` while DO canonical is `approved` — align display naming.

# 2. P1 — FINISH THE OWNER'S LAST ACCEPTANCE LIST
- [ ] Admin CMS Verified Buyer list shows name, mobile, email, address, country + Hard Delete + Add User / registry-claim review + distinct styling for registry-matched candidates.
- [ ] Add User (registry onboarding) matches on company name/email/mobile, creates NO duplicate shared identity, requires KYC/documents before authentication approval, and only then continues to GEID / Customer ID.
- [ ] **Registry matching is currently MOCKED** (`test_iter58_registry_matching_mocked.py`, `test_iter59_registry_claim_mocked.py`). Validate against a real authorized government data source before claiming it works.
- [ ] "Congratulations, your company is already a verified buyer" onboarding automation — unverified.
- [ ] Validate all notification templates with valid approved recipient addresses (test failures so far were recipient-domain policy, not workflow).

# 3. P1 — PRODUCTION / EXTERNAL VALIDATION (needs the new deploy)
- [ ] **PRE-PUBLIC-LAUNCH SECURITY (mandatory):** rotate `ADMIN_TOKEN` + `ADMIN_PASSWORD` to strong production values (Secrets tab → Redeploy); update `/app/memory/test_credentials.md`.
- [ ] Re-verify PRODUCTION Resend secrets — sender `admin@vametra.com`, mobile row, vametra.com footer links. Still unverified across several sprints.
- [ ] Weekly buyer notices + 1 AM IST pending-review digest — confirm over real runtime.
- [ ] Live DO / Firebase identity consistency between website and mobile app.
- [ ] Confirm `has_contact` engine guards live on prod (code guards needed the redeploy). Prod was pruned to 17,738 buyers, 100% contact.

# 4. P1 — PAYMENTS GO-LIVE
- [ ] Add LIVE Stripe secret key + Razorpay `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` (Secrets tab → Redeploy). Code is env-ready: Razorpay auto-activates for India, Stripe international. (Owner sourcing keys.)
- [ ] Live-test $105 (Stripe) + ₹10,000 (Razorpay) event-listing payments.
- [ ] Wire Razorpay checkout + webhook once keys arrive (gateway toggle + pricing already in the Pricing Engine).

# 5. P1/P2 — VERIFIED BUYER & CMS PRODUCT BACKLOG
- [ ] **Reviewer Console** — CMS screen for the human-review queue (`/api/verify/admin/queue` + `/decide`) with selfie + document side by side.
- [ ] **Verified Buyer Boost** — "Verified Member" badge + priority ranking across `/buyers` listings.
- [ ] **Reveal Limits** — per-plan monthly cap (`buyer_contact_reveals` logging already ready).
- [ ] **My Revealed Buyers** — saved list per subscriber.
- [ ] **Save to CRM / vCard export** on the reveal card.
- [ ] **Weekly Buyer Digest** (Resend).
- [ ] **Redeploy Safeguard** — verify-before-delete prune hardening pushed to prod.
- [ ] **Importers-as-Verified-Buyers** — registered importer users auto-listed (company, address, official email, contact, country, products, scorecard, badge) with explicit OPT-IN consent + user→buyer sync engine. Owner offered 5 test profiles.
- [ ] **My Reports history + shareable public/private links with expiry.**
- [ ] **VBIE France SIRENE / Japan NTA / Australia ABN** — flip on when owner provides keys (after marketing).
- [ ] **Web↔App deep linking (mobile phase)** — Android App Links + iOS Universal Links + Expo Linking on `/project/{id}` & `/report/{id}`. Do NOT use Firebase Dynamic Links (deprecated). Routes not implemented on web yet.

# 6. P2 — ENGINEERING HYGIENE / SCALE
- [ ] Paginate + cache `/admin/users` and the CMS buyer list (>~2000 users / growing buyer set).
- [ ] Warm `do_users_cache` on startup (today it fills on first main-admin Users load).
- [ ] Migrate `subscriptions.owner` to one canonical key (uid); legacy rows may use customer_id.
- [ ] Make DO calls in `_finalise()` async (httpx) instead of blocking `requests`.
- [ ] Return offending `submission_ids` in the allocation 400 detail.

---

# 7. PRODUCT VOLUMES (unchanged, parked)

## VOLUME 2 — TRADE SIMULATION & DECISION ENGINE (foundational, HIGH)
- **2A — DONE (2026-07-05)** Digital Twin, Scenario Builder (compare/merge/duplicate/archive/versioning), Trade Score Engine (8 explainable scores), Decision Engine, Universal Audit Trail, Live Data Adapter framework, Brain recommendations, Volume-2 PDF integration. Verified iteration_24 (19/19).
- **2B** Monte Carlo (FX, freight, duty, delay, commodity price, demand, volatility → Best/Expected/Worst + probability + confidence) + Sensitivity Analysis with Brain explanation.
- **2C** Trade Recommendation Engine (Incoterm/currency/route/mode/pricing/timing/buyer/supplier), Risk Simulation (political, currency, weather, compliance, supplier, buyer, port congestion, geopolitical, sanctions, disaster, container, banking, insurance), Trade Forecast (30/90/180/365-day).
- **2D** Interactive World Map (route/risk/demand/growth/opportunity heatmaps) + Volume 2 PDF integration.

## VOLUME 3 — GLOBAL TRADE INTELLIGENCE NETWORK
- **3A** Live Data Adapters: commodity, FX, freight, shipping, weather, ports, customs, govt, banking, insurance, trade agreements, import/export restrictions.
- **3B** Buyer Intelligence + Supplier Intelligence.
- **3C** Market + Country Intelligence (195 countries).
- **3D** Compliance Intelligence (country × product): docs, licenses, inspection, testing, certificates, permits.
- **3E** **Packaging Intelligence (mandatory)**: packaging checklist, primary/secondary/export packaging, palletization, container loading/type, wood treatment, fumigation, DG, hazard labels, UN markings, barcodes/QR, labelling rules, shelf life, temp/humidity, weight/stacking limits, cost + time, Brain recommendations, downloadable checklist.
- **3F** Documentation Intelligence (country/product doc set).
- **3G** Trade News (Brain-summarized global/product/country impact).
- **3H** Volume 3 PDF integration.

## VOLUME 4 — ENTERPRISE TRADE OS
CRM (customers/suppliers/leads/partners), ERP-ready (inventory/warehouse/purchase/sales/mfg), Workflow Engine (tasks/approvals/assignments/notifications), Team Collaboration (comments/mentions/approvals/version history), Document Management (OCR/AI search/classification), Executive Dashboard, Enterprise APIs (ERP/SAP/Oracle/Microsoft/Tally/Zoho/QuickBooks), White Label, Enterprise Security (RBAC/audit/logs/encryption/SSO) + Volume 4 PDF integration.

## UNIVERSAL PDF ENGINE (cross-cutting)
Cover + branding, project + exec summary, full Incoterm costing (EXW/FOB/FCA/FAS/CFR/CIF/CIP/DAP/DPU/DDP), landed cost, taxes/duties/FX/insurance/freight, simulation, scenario comparison, risk, trade health, compliance, packaging + documentation checklists, buyer/supplier/country intelligence, trade news, Brain analysis, recommendations, next steps, charts, appendix, disclaimers, Report ID, QR, date, page numbers.

**Deliverables per volume:** updated blueprint · architecture diagrams · DB design · API contracts · Brain integration · PDF integration · test report · completion checklist.

---

# 8. DONE (kept for reference, do not rebuild)
- [x] Production polish sprint (2026-07-14) — scroll-to-top, per-page SEO + JSON-LD, llms.txt, route lazy-loading, social links via `lib/brand.js`. iteration_27 13/13.
- [x] Legal pages (2026-07-05) — Privacy, Terms, Cookie, Disclaimer, Refund at `/legal/*`.
- [x] Analytics wiring (GA4 + GTM + Clarity, consent-gated, verified firing iteration_46).
- [x] `has_contact` engine enforcement on bulk loader + daily ingestion + search guard (iteration_47).
- [x] Verified Buyer flow `/verify` wizard + admin queue + live DO GEID link (iteration_48).
- [x] Admin Phase A (staff auth/RBAC, Users tab, scopes, search), Phase B (Allocate panel, sub-admin lifecycle, pending-review categories, nightly digest), Phase C (two-tier sign-off, per-user actions, Brain-owned user comms, email templates), Phase D (one record per user, two-tier hard delete, TEST flags, export). iterations 54–56.
- [x] Admin 401 canonical-role fix + `GET /api/admin/whoami` diagnostics.
- [x] Users tab hydration from canonical DO registry + shared `profiles` (iteration_55).
- [x] Cookie banner hidden for staff/admin routes.
- [x] Bulk main-admin approvals, sub-admin free-month subscription requests, shared `approved` status sync, CMS Verified Buyer list + registry-match onboarding scaffold, hard-delete resiliency, main-admin token precedence fix — SHIPPED, agent-tested (iterations 57–62), **awaiting the §1 validation above**.
