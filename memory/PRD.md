# Vametra AI / LeadNation — Product Requirements & Current State

Last updated: **2026-09-30**. Historical detailed requirements and implementation evidence formerly in this file are preserved verbatim in `PRD_HISTORY_PRE_MOBILE_2026-09-30.md`. See `CHANGELOG.md` for milestones and `ROADMAP.md` for the prioritized backlog.

## Original product and users
Vametra AI is a global trade-intelligence website for importers, exporters, suppliers, learners, and administrative staff. It provides AI trade advice, a project-based Trade Command Center, verified buyer discovery, customs/duty/landed-cost tools, country/product intelligence, trade news, upcoming expos, business services and a free Trade Academy. The public brand/domain is Vametra AI / vametra.com; internal LeadNation identifiers remain unchanged.

## Architecture and non-negotiable contracts
- React 19 / React Router frontend, FastAPI backend (`backend/server.py`), MongoDB local overlays/cache/settings/service data.
- Frontend APIs use `REACT_APP_BACKEND_URL`; backend routes are `/api/*`. Database uses existing `MONGO_URL` and `DB_NAME` without renaming either.
- DigitalOcean shared identity APIs own canonical user/company identity, Customer ID, GEID and authoritative profile readbacks. Firebase handles buyer sign-in. Website-local staff use separate JWT auth. No competing identity stores.
- Never treat local `members_bridge` snapshot as authoritative identity truth. Canonical verification statuses are `approved` / `rejected` (some legacy UI uses verified).
- Preserve subscription/contact gates, source privacy, legal acknowledgment, admin sign-off rules, pricing overrides and established design language.
- New dropdowns must use `components/ui/responsive-select.jsx`; geographic fields use `components/LocationSelect.jsx` and `data/geo.js`. Do not add short hardcoded country arrays or browser-native form selects to app pages.
- Use unique `data-testid` values for interactive/critical UI elements. Preserve API value contracts (ISO codes vs names; lowercase codes for news).

## Latest owner request — verbatim
“The website is currently not functioning well in mobile view. If the user is checking the website on mobile, in that case the user is not able to select any dropdown, nor are they able to see the options in the dropdown on any page/function/tab/onboarding process anywhere.

Also from now on, please add all the 195 countries/states/cities, etc in the in all the respective dropdowns.

make sure the mobile view should be the perfect for all the users.”

Owner approved proceeding with a site-wide mobile dropdown repair, comprehensive countries plus territories, dependent state/city choices and manual entry for missing localities. Unrelated Academy/Brain, marketing, and prior admin workflow engineering remain parked.

## Latest milestone — implemented and verified, awaiting owner acceptance
### Mobile dropdowns and geography (2026-09-30)
- Replaced all **58 native select call sites in 22 pages** with a shared Radix Dialog + cmdk picker: touch targets, searchable readable options, independent scrolling, keyboard navigation, Escape/cancel, focus return, high stacking above admin modals/cookies, and visual-viewport keyboard sizing. Existing handlers/value contracts preserved.
- Applied across signup roles/dial codes, verification role/doc/location, account, Expo, news, buyers, customs/tools, Command Center and admin/pricing/action forms. Country text inputs in Brain, account, directories/suppliers and CMS also use the common country selector.
- **250 countries/territories** (including all 195), **4,963 subdivisions**, **148,038 city records** from country-state-city 3.2.1 (ODbL). This is NOT a claim to list every settlement worldwide. State/city search permits explicit custom entries and retains manual entry if loading fails.
- Country list bundled locally; each country's states/cities loaded on demand from `/geo/{ISO}.json`. No third-party geo credentials/network API. Generator `frontend/scripts/generate-geography.cjs` reproduces frontend/backend catalogs and license files.
- Country change clears state/city; state change clears city. Explicit empty locality fields included in verification/admin profile save payloads so old localities are not silently retained. Existing profile values remain displayed; no saved user profiles changed during tests.
- `/api/countries`, `/api/duty/countries`, `/api/command-center/markets`, `/api/news/countries` each return 250 unique countries. Existing business-calculation coverage/rate data are NOT fabricated or expanded. Event queries match ISO/full-name/legacy aliases (e.g. AE/UAE/United Arab Emirates).
- Mobile header no longer overflows: fixed `.btn-*` overriding hidden utilities, accessible menu toggle, mobile account link, Explore/Learn tap groups, pointer-aware wide-screen navigation. Floating Brain/WhatsApp launchers hidden on small screens so they cannot obstruct form controls; Brain/contact access remains in navigation/site content.
- Fixed signup flex-width overflow, bounded decorative effects, and stabilized Expo country choices during asynchronous hydration.

### Test evidence
- `test_reports/iteration_67.json`: initial agent run, 14/15 API tests plus broad mobile touch/public/auth/admin selector regression; identified country endpoint mismatch, Expo first-open concern, tablet grouping and an onboarding test gap.
- **Final API rerun: 15/15 passed**, `test_reports/pytest/iter67_retest.xml`, `test_reports/iter67-retest.log`. Four country endpoints each independently checked for 250 unique codes. All three UAE aliases returned the same 5 events.
- Main-agent browser follow-up resolved onboarding test gap using the REAL existing account (no fixture): France → Île-de-France → Paris, country reset, role selection. Save payload check intercepted and **aborted** the PUT before the server; verified country/state/city keys, without writing user data.
- Mobile touch signup selection (Armenia/Zimbabwe) and role options, desktop keyboard Arrow/Enter, Escape and focus return, mobile Explore/Learn groups, and first-tap wide-screen touch navigation passed.
- Expo initial-open options checked repeatedly (251/252 entries including All/legacy labels), country selection/clear passed. No persistent empty list reproduced when waiting for visible options; country-choice memoization removes unnecessary hydration churn.
- **Zero horizontal overflow** in final 390×844 verification/Expo checks and 1920×800 Expo check. Screenshots: `onboarding-mobile-check.jpg`, `mobile-final.jpg`, `expo-desktop-final.jpg`, `dropdowns-mobile.jpg`.
- Production frontend build passed (pre-existing hook-dependency warnings / large-main-bundle warning remain). Latest payload-only changes also exercised in browser.
- Safari/WebKit browser binary is unavailable in this environment; actual iPhone/Safari and physical Android testing remain owner acceptance checks. Do not claim all physical devices were tested.
- No app APIs/integrations were mocked for this milestone. No auth credentials created/changed; no prices, user profiles or verification statuses mutated. Full verification submission, payments and email delivery were intentionally not exercised.

## Previous completed milestones
- Business Services pricing editor + Business Website service (India ₹35,000/year, international US$2,500/year, 11 scope items), iteration66: 9/9 backend + frontend verified; owner acceptance pending.
- Homepage visual redesign/motion/mobile work, free Trade Academy section replacing “See trade happen”; “Engineered for India” removed.
- Verified Buyers source categories + required legal/data-usage acknowledgment, frontend-only; buyer data/verification logic preserved.
- Product Info frontend retired; product intelligence consolidated into Brain. News country/topic/live freshness; Expo live/upcoming refresh and admin notification records.

## Integration status and limitations
- DigitalOcean + Firebase: existing authoritative identity/auth, untouched by this milestone.
- Resend: admin notification records evidenced; actual recipient inbox delivery remains unconfirmed.
- NewsData key was empty in previous checks; Google News RSS + GDELT provide live news; GDELT may fail gracefully.
- Government registry matching remains **MOCKED / not live-validated** from prior work; requires authorized registry access. This is unrelated to location data, which is real offline reference data.
- Never rerun destructive old tests57–62 against deleted fixtures. Credential/status source: `test_credentials.md` (private).

## Tools rewire — 8 Oct 2026 (iteration 70, 25/25 backend + all frontend flows passed)
- Every `/tools/*` page now embeds the REAL Customs & Compliance Engine components (shared `components/engines/CustomsEngineTools.jsx`): Duty (WITS+RoDTEP), Landed Cost = Command Center quote, Product Research = OEC Trade Statistics, Incentives = RoDTEP+Govt benefits, Buyer Discovery = real `/api/buyers/search`. No duplicated logic; each page has "Open in full Customs & Compliance Engine" (`/customs-compliance?tab=`).
- HSN Finder: all 5,606 HS codes + trade-name alias layer (`TRADE_ALIASES`) + DGFT RoDTEP + IGST slab + live WITS duty at destination. `/api/hsn/{code}` now works for any HS6 (curated knowledge merged for 5 flagship lines).
- Country dropdowns for duty/command-center lanes use `/api/duty/countries` (56 WITS countries, ISO-numeric) via `LaneCountrySelect` — the old alpha-2 list silently returned no data.
- "Vametra AI Brain · next steps" panel (`POST /api/tools/next-steps`) under every result: AI read of the user's numbers (Emergent key, falls back to deterministic text) + pre-filled links to the next tool/buyers/export guide/Brain + plan upsell. Fires `tool_next_step` / `upgrade_cta_click` analytics events.
- Removed mock endpoints: `/duty-calc`, `/landed-cost`, `/export-incentive`, `/product-research`, `/find-buyers` (legacy tests in `tests/test_leadnation_api.py` for these are obsolete).
- **Global, not India-centric (owner rule 8 Oct):** every tool must take exporting + importing country; India-specific schemes (RoDTEP, IGST) appear only when India is the origin/destination. HSN Finder updated accordingly.
- Rule going forward (owner): never build duplicates; every feature must be useful for marketing and route to signup/plan.

## SEO pre-render reliability — 10 Oct 2026 (29/29 pytest)
- Export guides were served as a bare SPA shell to Googlebot because `/api/seo/page-data` had no
  cache and a cold WITS duty lookup took ~15s, longer than the edge pre-render worker waits.
- Now: 24h `db.seo_page_cache`, concurrent section fetch, `POST /api/seo/warm-pages`, a boot+daily
  warm job, and a global WITS concurrency gate so warmers cannot starve the event loop.
- All 448 product x country payloads pre-built (400 indexable); page-data responses ~0.23s.
- **Needs a production deploy** — the boot warmer then runs 8 min later. Re-audit afterwards.
- Full detail in `CHANGELOG.md` (2026-10-10) and `PRERENDER_ESCALATION.md`.

## GSC rich-result + head hygiene — 10 Oct 2026 (preview verified, needs deploy)
- GSC confirmed `/export/indian-spices/to/chile` is indexed and fully rendered (prerender fix worked).
- GSC "Product snippets: 1 invalid item" → `about` was `@type: Product` without offers; now `Thing`
  (ExportProductCountry, Products.jsx, SEO.productSchema).
- Crawled HTML had two `<title>`/description/og sets: React 19 hoists Helmet tags and does not dedupe
  the static ones in `public/index.html` → static title/description/og/twitter removed; every public
  page renders `<SEO>`; admin pages got `<SEO noindex>`.
- BreadcrumbList pointed at `/products/indian-spices` (not a real page) → now `/export` → `/export/{product}`.
- New `/api/answers/index.html` (HTML directory of 413 answer docs) for AI browsing tools that refuse JSON.

## Production verification — 10 Oct 2026 late (`memory/audit_2026-10-10/REPORT.md`)
- Googlebot full audit: 392 guides → 381 rendered / 11 shell / 0 errors; 15 hubs OK. Shells = cold page-data
  holes that the edge then cached (`x-rendered-by: crawler-cache`, max-age 3600). 413 answer docs all clean.
- Fixes (preview only, NOT deployed): stale-while-revalidate page cache + 6-hourly retrying warm;
  rail links only to existing `/countries/*` (5) and `/corridors/*` (4) — 44/49 countries were soft-404s.
- Open owner decision: SoftwareApplication `aggregateRating 4.8/126` provenance.

## Brand consistency + AI readability + cache warming — 15 Oct 2026 (preview verified, NOT deployed)
- Brand facts everywhere: founded 2026, HQ "Savedi, Ahilyanagar, Maharashtra 414003, India" (short form,
  also Legal.jsx + llms.txt), founder Vaibhav Deshmane, LinkedIn display `linkedin.com/company/vametra.com`.
- "195+ countries" removed from all 22 places (12 files) → "contact-verified buyers across 32 countries" /
  "56 tariff-reporting countries". Camera/imaging FAQ + paragraph removed from /about.
- llms.txt: fixed false "Platforms: Web, iOS, Android" → web only; added /about + its answer doc.
- New `/api/answers/{md,html,json}/about` entity document (index now 414; sitemap unchanged at 974).
- Cache warming: page-data warm now oldest-first, 4 concurrent, 250 ms stagger, run log in `seo_warm_runs`;
  NEW prerender warm of 34 key static pages (Googlebot UA → vametra.com) every 45 min (:05/:50) + 2 min
  after boot; admin `GET /api/seo/warm-status`, `POST /api/seo/warm-prerender`. First run: 34/34 OK,
  7 were cold (6–12 s) and are now cached — this was the "cache miss" ChatGPT hit on /about.
- Backlog: Google Business Profile (revisit when eligible); Home "32K HS Codes" / "1.2M Data points" stats unverified.

## Part 6 — answer-first rewrites — 16 Oct 2026 (preview verified, iteration_75, NOT deployed)
- 71 pages: keyword-led titles ≤60 + H1 with keyword (`data/seoTitles.js`, `seo/PART6_PAGE_PLAN.md`), `AnswerFirst`
  block (direct answer + dated data table from new `GET /api/seo/facts` + 5 links) on 28 templates, FAQPage/Breadcrumb.
- Soft-404 hardening on 8 detail templates via `loadEntity()`; genuine not-found now `noindex`; loading state = final title.
- Nav bell only when logged in. CTARow "Download app" removed. Home stats → 5,606 HS codes / 56 tariff countries.
- Prerender warm now 56 key pages. Acceptance report: `memory/seo/PART6_ACCEPTANCE.md` (15/16 pass, #16 after deploy).

## Priorities / next actions
- **P0:** Deploy, then Googlebot-render audit of the 71 Part-6 URLs + `/about` as GPTBot; `/api/answers/md/about`.
- **P0:** Deploy, then: GSC "Validate fix" on Product snippets, re-run `audit_2026-10-10/guides_audit.py`
  once the edge shell cache has expired (or ask platform to purge the 14 URLs), re-inspect 3 guides.
- **P0:** Deploy, then re-audit the export guides with Googlebot UA and report rendered/shell counts.
- **P0 (marketing Part 6):** answer-first rewrites of the older pages + the 16-item acceptance report.
- **P0:** Owner mobile-device acceptance (iPhone/Safari and Android); latest admin-pricing acceptance still pending. Any newly reported mobile defect takes priority.
- **P0 (SEO plan):** Part 3 server-side pre-rendering for SEO routes → Part 4 region hubs/country pages → Part 5 product×country batch. See `memory/seo/EXECUTION_PLAN.md`.
- **P1:** Fresh vametra.com marketing/SEO/GEO plan (do not recycle leadnation.app plan); Academy ↔ Brain coordination remains backlog-only; Expo email inbox validation.
- **P2:** International Expo pricing; localized location names and reproducible geographic-data refresh; optional remembered recent countries.
- Frozen until expressly requested: broad admin/buyer approval regression, hard-delete consistency, CMS volume/timeouts, live registry integration, subscription/payment changes.
## 2026-06 Nav fix
- Fixed clipped "Explore Vametra AI" CTA in desktop nav (Nav.jsx): tightened logo/link padding and action gaps; CTA shows short "Explore" label between lg and xl widths, full "Explore Vametra AI" at 2xl+, so the nav row now fits inside the max-w-7xl container at every desktop width.

## 2026-06 Smart HS resolution (any product name)
- New backend/hs_resolver.py: HS6 resolution tiers — directory phrase match -> LLM classifier -> Gemini web-grounded lookup -> residual "n.e.c." heading in the same HS heading; every candidate validated against the HS directory, results cached in Mongo (hs_resolver_cache, 180d hits / 3d misses).
- Wired everywhere: /api/trade-intel/hs-search (typeahead fallback), /api/hsn-finder (+resolution banner), brain/explore (hsResolution + classification note), brain/engines, costing_engine, compile_engine.
- Local/misspelled names now work: brinjal & bringle -> 070930, okra & bhindi -> 070999, basmati rice -> 100630; nonsense input stays unresolved (no fabricated code). Duty/demand still only from WITS/OEC.
- Also added BrainThinking loading animation on /brain/explore. Verified by testing agent iteration_77 (backend 7/8 - one cold-start timing bound, frontend 100%).

## 2026-06 Alias memory for HS resolution
- New Mongo collection hs_aliases: every resolved product name (the query, the canonical name and each alias the classifier returned) is stored, so repeats like bhindi/bhindis/ladies finger answer from memory (~0.7s) with no AI call.
- Plural/possessive-insensitive normalisation; derived names only fill gaps (never overwrite a proven mapping); seeded at boot from the published product catalogue (39 names).
- Classifier accuracy guards added: raw-form default (no frozen/dried/prepared line unless the user said so), prepared-chapter guard (16-21), residual "miscellaneous/n.e.c." heading fallback. Verified: okra/bhindi 070999, brinjal 070930, tinda 070993, pomegranate 081090, frozen okra 071080, mango pulp 200899.

## 2026-06 Service request email (single combined mail)
- POST /api/service-request now sends ONE email: To admin@vametra.com, CC the requester, reply-to the requester, subject "Vametra Service Request · {Service}".
- Body carries the full request (service, request ID, submitted time, notes), contact details (name, email, phone, company, country) and the Vametra profile block (customer ID, registered mobile, plan, email-verified, KYC, member since) when the email matches an account; CTA is WhatsApp so it suits both recipients.
- emailer.send() gained cc/reply_to support and a shared _rows() detail renderer; Services.jsx success note now tells the user a copy was emailed to them.
- Verified: live Resend send returned an id; endpoint returns ok for both catalogue and non-catalogue service slugs.

## 2026-06 Service request email v2
- Removed every CTA button from the service-request email (no "Open admin"); deleted the legacy admin_service_request template so only the combined mail can fire.
- Requester email now appears in the Contact block, in the closing line and in CC; profile block widened to read db.users -> do_users_cache -> profiles (account name/email, customer ID, mobile, role, plan, email verified, verification status, company on file, location, products, member since) with empty rows dropped.
- NOTE: production still serves the pre-change build — a republish is required for the new email to go out live.


## 2026-06 Service request email v3 (identity fix)
- ROOT CAUSE of mismatched "Vametra profile" block: it was looked up by the email TYPED in the form, not the logged-in account; plus `profiles` collection holds stale data (pending/importer) vs `do_users_cache` (approved/exporter).
- Fix: POST /api/service-request now takes `optional_user` (Firebase bearer token, already sent by lib/api.js) and resolves the account from `do_users_cache` by uid. Request doc stores userUid / accountEmail / customerId (ready for sub-admin/CA allocation).
- Email is admin-only (no CC), reply-to = typed email, no buttons. Blocks: Request, Submitted details (typed form), Vametra account (Logged-in as / Customer ID / KYC status / Plan — only reliable fields; guests show "Submitted as guest"). Removed mobile/role/email-verified/member-since/profiles data.
- Verified: logged in as vaibhav@leadnation.app while typing krivajexim@gmail.com → stored accountEmail vaibhav@leadnation.app, customerId 00009; guest path 200.
- NEXT (user-stated): allocate landed service requests in admin portal to Sub-admins and CAs.

## 2026-06 Services catalogue accuracy + Udyam
- Company Registration: documents now grouped per entity via new `documentGroups` field (Shop Act / LLP / Pvt Ltd–OPC); Services.jsx renders groups (data-testid service-document-groups) with fallback to flat `documents`. Process steps clarified (RUN/SPICe+ not needed for Shop Act).
- Tightened documents for RCMC, GST, IEC (constitution proof, NOC, DSC notes, ANF-2A(I) bank cert).
- NEW service `udyam-registration` — Udyam (MSME) Registration, priceFrom INR 999 (editable via admin service rates), SEO entry in seoTitles.js, auto-included in sitemap/search.
- Services.jsx success message no longer claims a copy was emailed to the user (admin-only mail).


## 2026-06 Services page cleanup
- Removed "Process flow" card + "Process steps" answer-row from every service detail page (backend `process` arrays kept but unused).
- FAQs: removed every government-fee question/answer (IEC ₹500, Udyam free). Each govt-documentation service now has one positive "What does the Vametra AI fee include?" FAQ framed as a single all-inclusive fee (government + professional charges covered).

## 2026-06 Entity picker + documents note
- company-registration has `entityOptions`; Services.jsx shows a required <select data-testid=service-entity> only when present. ServiceRequest model has optional `entity`; stored on the request, shown as "Entity type" in the admin email and under Service in Admin > Service Requests.
- Documents card shows reassurance note (data-testid service-documents-note): "Missing a document? No problem..." on every service page.

## BACKLOG (user-requested, 2026-06) — REMIND USER after marketing part + service-request part are done
- DONE 2026-06: Allocate button + CA/Associate categories.

## 2026-06 Service-request allocation — PHASE 1 DONE (plan: SERVICE_REQUEST_ALLOCATION_PLAN.md)
- backend/service_desk.py (new router; admin.py endpoints moved): STATUSES incl. Partial/Full payment received; PUT /admin/service-requests/{id} {status, assignedCaId, assignedCa, assignedCaEmail, internalNote, clearCa} with history[] + notes[] + updatedBy; completed/cancelled block CA allocation (400); assigning CA while new ⇒ assigned. GET /admin/service-requests/ca-options ⇒ active sub_admins.
- frontend/src/pages/admin/ServiceRequestsManager.jsx (replaces inline ServiceRequests): filters (search/status/CA/service, Unassigned quick filter, no statuses hidden), CA dropdown (sub-admins + External CA… free text), editable CA email, Email CA button (disabled when closed / no email — wiring in Phase 2).
- NEXT: Phase 2 email-ca endpoint + preview modal (To editable, locked CC customer+admin, extra CC).

## 2026-06 Allocation PHASE 2 DONE
- POST /admin/service-requests/{id}/email-ca {to, extraCc[], note, dryRun}: dryRun returns {subject, html, to, cc, lockedCc}; real send via Resend template service_allocation (subject "Vametra Service Request · <Service> · Allocated to Vametra CA"), CC forced = customer + admin@vametra.com (+extra), reply-to customer; logs emailActivity[], caNotifiedAt, history; closed requests 400; send failure 400 (never 502 — proxy swallows it).
- services.py stores profileRows + serviceLabel on each request so later emails reuse identical data (service_desk.request_email_ctx).
- EmailCaModal.jsx: To editable, locked CC chips, extra CC, note, live iframe preview, Send ▸. Button in ServiceRequestsManager.
- Fixed: no sonner <Toaster/> was mounted app-wide — added in App.js (toasts now show everywhere).
- Tested: iteration_78.json 15/15 backend, frontend all pass; 1 real send OK.
- NEXT: Phase 4 (sub-admin Service Requests tab) then Phase 3 (drawer), status-change customer emails.

## 2026-06 Allocation PHASE 3 DONE
- frontend/src/pages/admin/ServiceRequestDrawer.jsx (shared, props: item, meta, onSave, onEmailCa, caReadOnly, canEmailCa, extraActions — ready for sub-admin reuse in Phase 4). Sections: Status & allocation (status select, CA, Email CA, CA notified), Request, Customer (copy email), Vametra account (profileRows), Internal notes (add → PUT internalNote), Email activity, History timeline. Mobile-safe.
- ServiceRequestsManager: row click opens drawer (control cells stopPropagation). Verified desktop + 390px.
- NEXT: Phase 4 sub-admin Service Requests tab (reuse drawer with caReadOnly + Email customer action), then status-change customer emails.

## 2026-06 Conversation (email chat) in drawer DONE
- service_desk.send_customer_message(item, message, extra_cc, sender_name, sender_email, sender_role, dry_run) — SHARED for admin + Phase 4 sub-admins. To=customer, CC forced admin@vametra.com + assigned CA email (+extra), Reply-To=sender. Template emailer BUILDERS["service_message"] (same subject "… · Allocated to Vametra CA" so inboxes thread; message block HTML-escaped + full request body). emailActivity entry kind=message with text/byName/role; history + lastMessageAt.
- POST /admin/service-requests/{id}/email-customer {message, extraCc, dryRun}.
- Drawer "Conversation with customer": chat bubbles (customer request first, then allocation + message emails), composer + extra CC + Send email. Inbound customer replies are NOT captured (go to Reply-To inbox) — backlog: Resend inbound webhook to pull replies into thread.
- Verified dryRun/400/real send + UI.

## 2026-06 Allocation PHASE 4 DONE + Allocate button (iteration_79: 15/15 backend, frontend all pass)
- Allocate: POST /admin/service-requests/{id}/allocate {assignedCaId | assignedCa+assignedCaEmail, note, sendEmail, extraCc} — assign + optional allocation email in one step; resets openedBy. AllocateModal.jsx; "Allocate"/"Re-allocate" button in row + drawer.
- Staff endpoints (require_staff; sub-admin scope assignedCaId==sid, 403 otherwise): GET /staff/service-requests {items(isNew), statuses, me}, GET /staff/service-requests/summary {open,new,unassigned}, POST /staff/service-requests/{id}/open, PUT /staff/service-requests/{id} {status, internalNote} (completed final for sub-admin), POST /staff/service-requests/{id}/email-customer (sender = CA name, role CA, Reply-To CA, CC admin + CA).
- PERMISSIONS extended (service_requests.*). ServiceRequestsManager mode="staff": no CA filter/controls, "You" column, NEW badge, Open · Email customer; drawer caReadOnly, statusLocked. SUB_TABS += Service Requests; tab badge (sub-admin: new count, main: unassigned count).
- NOTE: Python scripts writing to /app files are blocked by harness — use search_replace/create_file.
- Remaining from plan: status-change customer email (Partial/Full payment/Completed) with Notify toggle; inbound reply capture (backlog). BACKLOG reminder: CA/Associate categorisation.

## 2026-06 Sub-admin management moved to Dashboard + CA/Associate categories (BACKLOG ITEM DONE)
- backend/subadmin.py: CreateSub.category (CA|Associate, required valid), SubPatch.category; list returns category + service_requests_open. ca-options returns category (sorted CA, Associate, Uncategorised).
- frontend SubAdminsManager.jsx rendered on Dashboard tab (create with CA/Associate toggle, list with category badge, Set category select, active toggle). AllocatePanel (Users tab) no longer creates sub-admins (hint text). AllocateModal options prefixed "CA · name · email"; row CA dropdown shows "(CA)/(Associate)". PatniCA=CA, Sakshi=Associate set in DB.
