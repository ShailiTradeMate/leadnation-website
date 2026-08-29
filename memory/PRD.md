# LeadNation — Global Trade Intelligence Portal

> 2026-06 UPDATE — ADMIN PANEL **PHASE B** — BUILT & TESTED (iteration_52, backend 17/17, frontend 100%). **Allocation:** main-admin-only "Allocate" button in the User Section opens `AllocatePanel` — (1) select active sub-admins (checkboxes) → round-robin distribute all unassigned `needs_review` submissions (sets `assigned_to`/`assigned_to_name`) + best-effort `subadmin_allocation` notification email per sub-admin; (2) create sub-admin (name/email/password) + activate/deactivate toggle (inactive → excluded from allocation list + login blocked). **Nightly digest:** `send_pending_digest()` emails admin@vametra.com the pending-approval COUNT, cron 19:30 UTC = 01:00 IST (`start_pending_digest`), no per-user/sub-admin emails. Fixed `admin_users()` to rank submissions per uid (assigned/needs_review win over rejected) + surface applicant submissions with no registered user, so sub-admin allocation scope shows correctly. Endpoints (main-admin only, 403 for sub-admins): `GET/POST /api/admin/subadmins`, `PATCH /api/admin/subadmins/{id}`, `GET /api/admin/allocate/pending`, `POST /api/admin/allocate`. ⏳ Phase C (per-user Approve/Reject/Hard Delete/Contact/Edit/Payments+free-sub grants) pending review-gate. Known cosmetic: cookie banner overlaps table bottom until dismissed.

 — BUILT & TESTED (iteration_51, backend 100% 12/12, admin frontend 100%). Website-local **sub-admin auth** (bcrypt + JWT in Mongo `sub_admins`, `/app/backend/subadmin.py`) — fully separate from DO/Firebase buyer identity & Customer IDs. `require_staff` accepts EITHER a Firebase main-admin Bearer OR a sub-admin `X-Staff-Token` (reusable RBAC for future CMS sections). Endpoints: `POST /api/admin-auth/login`, `GET /api/admin-auth/me`, `GET /api/admin/users?q=`. Seeded sub-admins **sakshi@vametra.com** & **patnica@vametra.com** (pwd Shiv@12345). **User Section** (`UsersManager.jsx`) shows ALL registered users (aggregates shared `db.users` + `verification_submissions` + `profile_overlay` + `subscriptions`), status label incl. **Not Applied**, real-time debounced search (email/mobile/User ID/company/name/country), expandable full-profile+documents detail. `/admin-login` has **Main Admin / Sub-Admin tabs**; sub-admins see ONLY the Users tab and only users allocated to them (Phase B adds allocation). Main admin (00001) sees everyone + all CMS. Sender-email + mobile-capture fixes shipped earlier this session. ⏳ Phase B (Allocate panel + sub-admin CRUD + nightly 1AM IST digest) and Phase C (per-user Approve/Reject/Delete/Contact/Edit/Payments) pending user review-gate.


> 2026-06 UPDATE — VERIFIED BUYER "PART 1" (user-side) — BUILT & TESTED (iteration_50, backend 100% / frontend 92%). Scope done: (1) **Signup prefill** — Verify profile Step 0 now shows a "From your account" card (email/mobile/category) so users don't re-enter; email falls back to Firebase user (`account.user.email`/`fbUser.email`) when DO profile is degraded. (2) **Country dropdown + dependent State/Province dropdown** (`frontend/src/data/geo.js` — India/US/UAE/Canada/Australia have state lists; others free-text). (3) **Company Name / Email / Contact + optional Address** collected & persisted. (4) **Website-local supplement store** `profile_overlay` (Mongo) — verify.py `_profile()` merges DO profile (canonical) + overlay (fills gaps only); DO still owns uid/email/customer_id/role. `_save_overlay` mirrors business fields on PUT/submit so completion% & re-checks stay stable even if DO drops fields. (5) **Doc name-mismatch → Admin Review** — `analyze-document` sets `name_mismatch`+`expected_company_name`; `_decide()` returns `needs_review` on mismatch (NEVER auto-verify). (6) **Welcome email** on submit (`verify_submitted` Resend template: User ID, mobile, email, country, document name). (7) **Weekly digest** `send_weekly_digest()` — verified members only + `notify_opt_in!=False` (opt-in checkbox on Step 3); APScheduler Mon 08:00 UTC via `verify.start_weekly_digest()`. Verified status is INDEPENDENT of subscription; public buyer DETAILS still require verified + active subscription (existing VBIE paywall). ⚠️ UPSTREAM (DO team): GET /v1/profiles/{uid} returns email/mobile/customer_id=NULL for test uid SPKdrHke3NNjWTpYwxHUzwLnZbO2 → prefill mobile + welcome-email User ID/mobile show "—" (website merge is correct; email now self-heals via Firebase fallback). Admin allocation/approve-reject/payment-popup UI = deferred "Part 2".



> 2026-08-20 UPDATE: Verify wizard now supports live CAMERA capture (selfie on all devices; documents camera on mobile only, desktop shows a phone tip) + file upload; a "Please stay tuned (1–2 min)" wait panel with a GK trivia quiz shows during AI checks; Admin login has Google sign-in REMOVED (ID/email + password only) and the admin email is admin@vametra.com; a new admin **Verifications** tab (Reviewer Console) approves/rejects Verified-Buyer requests. Customer-ID auto-heal broadened (any signed-in user w/o ID triggers DO /onboarding/register) + AccountPage now shows a "Retry" affordance on failure. ⚠️ TWO DO-BACKEND BLOCKERS remain (DO team must fix): (1) DO CORS does not allow https://vametra.com / www — breaks admin login + all auth on the production domain (preview origin IS allowed); (2) DO POST /api/onboarding/register returns HTTP 500 for new UIDs — 5-digit Customer ID never allocates. Both verified via iteration_49.json.

> ⚠️ REBRAND (2026-08-19): Public brand is now **Vametra AI** (legal: Vametra AI Technologies Pvt. Ltd.), primary domain **https://vametra.com**. All customer-facing "LeadNation" text/SEO/assets/emails were rebranded to Vametra AI. INTERNAL identifiers stay "LeadNation" (MongoDB `DB_NAME=leadnation`, DO identity backend host, Firebase project `trademate-new`, `LN-` GEID prefix, admin login `admin@leadnation.app`, internal code/collections). Email addresses + social handles kept on leadnation.app until Vametra Resend domain + social accounts are ready. Full migration checklist: `/app/memory/VAMETRA_REBRAND_CHECKLIST.md`. Historical entries below still say "LeadNation" for context — treat them as the same product now branded Vametra AI.


## VERIFIED BUYER COMPLETION + VERIFICATION — REFERENCE BUILD (2026-08-18, iteration_48 PASS 95%)
Owner directive: build the FULL importer-as-Verified-Buyer flow on the WEBSITE as a working reference that the DO/app team will mirror into the shared DO identity backend. Website stays a client of DO; DO still owns identity/profile/GEID.
- **App-team API status (confirmed live on DO `https://leadnation-lfrhs.ondigitalocean.app/api`):** GET/PUT `/v1/profiles/{uid}` (auth: Firebase Bearer + `x-user-uid` header; PUT requires x-user-uid == path uid), GET `/v1/documents` (personal/business/trade doc catalog, country-specific), **GEID linking LIVE**: `POST /entities` (member_company/prospect) + `POST /members/bind {uid,customer_id,geid}` → returns real GEID e.g. `LN-prospect-01M0...`. NOT built on DO yet: object-storage upload, selfie/liveness/AI-fake/duplicate-face, document OCR gov cross-check + review workflow.
- **Backend reference (`/app/backend/verify.py`, prefix `/api/verify`; `/app/backend/verify_ai.py`):** `GET /state` (proxies DO profile + computes completion %), `PUT /profile` (proxies DO PUT, now retries 5xx x3), `POST /upload` (Emergent Object Storage via existing `storage.py`, NOT base64), `POST /analyze-selfie` (gpt-5.4 vision: is_human_face, ai_generated_likelihood, quality, liveness, confidence + dependency-free 8x8 average-hash duplicate-face check vs `verification_face_index`), `POST /analyze-document` (gpt-5.4 vision OCR + legitimacy), `POST /submit` (re-runs checks server-side, decides verified/needs_review/rejected, on verified links GEID via DO), admin `GET /admin/queue` + `POST /admin/{sid}/decide` (human review → approve links GEID). Collections: `verification_submissions`, `verification_face_index`. Env added: backend `.env` `AUTH_API_BASE`. Decision thresholds: auto-approve ≥0.75, AI-fake ≤0.35, quality ≥0.40, doc conf ≥0.40, face Hamming ≤8.
- **Frontend (`/app/frontend/src/pages/VerifyBuyer.jsx` route `/verify`, `lib/verifyApi.js`, `components/VerifiedBadge.jsx`):** 4-step wizard (Profile completion → Selfie → Document → Consent+Submit → Result). Entry points: AccountPage `account-verify-cta` card + header badge; Nav `nav-get-verified` link. Role decoupled from step progression (persisted at submit) so DO write blips don't block. Required completion fields = name, mobile, email, country, city, products, company_details.company_name (dropped role + company_details.address — DO doesn't persist address).
- **Verified E2E:** backend curl (profile proxy, real selfie vision PASS, invalid cert correctly rejected→needs_review, admin approve→REAL DO GEID `LN-prospect-01M0BHNNNRZ...`). Frontend iteration_48: login+wizard+gating+result+auth-guard all work (95%). Fixed the one HIGH issue (DO PUT 502 coupling) via backend retry + frontend no-op-skip.
- **Known/handoff:** DO `PUT /v1/profiles/{uid}` intermittently 502s (upstream stability — flagged to app team). DO returned entity type `prospect` for an importer (`member_company` requested) — DO owns entity typing. Cookie banner overlaps wizard bottom on small viewports (pre-existing site-wide). Test acct: vaibhav@leadnation.app / Shiv@12345 (uid SPKdrHke3NNjWTpYwxHUzwLnZbO2).
- **NOT deployed to production yet — needs redeploy.** Follow-up app-team prompt saved at `/app/memory/APP_TEAM_PROMPT_VERIFY_PHASE2.md`.



## PROD FIX — Reveal Contact for ALL buyers + safe prune (2026-06, iteration_45 PASS)
User (as active subscriber vaibhav@leadnation.app) hit "Reveal contact details" on PRODUCTION (leadnation.app) and got nothing for a UK Companies House buyer (AK EXPORTS LTD).
- **Root cause:** Production DB was a separate/older copy — 19,165 buyers but only 4 had stored contact (the earlier preview enrich/prune never ran on prod). Companies House records have no published email/phone, so reveal returned nothing.
- **Fix:** Ran `POST /api/buyers/admin/contacts/enrich-prune` against PRODUCTION. Result: enriched 15,432 buyers with real email/phone from source, **deleted 3,729 no-contact buyers**, preserved the 4 pre-existing contact buyers, **0 admin/curated buyers removed**. Production now: **15,436 buyers, 100% with verified contact.** Verified via curl: subscriber vaibhav reveal → 200 with real email; AK EXPORTS LTD gone.
- **Safety hardening (user demand: never delete a buyer that has contact):** `vbie_contacts.enrich_and_prune()` now (a) sets `has_contact=true` for ANY buyer whose contact object has a non-empty email/phone (protects legacy/admin contact), and (b) deletes ONLY buyers verified to have BOTH `contact.email` AND `contact.phone` empty/missing, never `admin_edited`/`admin_deleted`. Verified by testing agent: a buyer with contact can never match the delete query. (This hardened code is in preview; prod migration already completed safely with prior logic — redeploy to carry the hardening forward.)
- **Forward rule (already enforced):** `run_ingestion` skips candidates without email/phone (`skipped_no_contact`), so new daily buyers are only kept if they have contact.
- **Reveal-quota readiness:** every reveal is logged to `buyer_contact_reveals` {uid, geid, at} — foundation is ready to add a per-plan monthly reveal limit next.



## VBIE — SOURCE PRIVACY + CONTACT REVEAL (2026-06, iteration_44 PASS)
Owner mandate: NEVER expose the data source or a source link — it let subscribers bypass LeadNation and pull buyers from the free government site. Buyers must only be kept/shown if they have contact details.
- **Source hidden everywhere.** `_full`/`_card`/locked payloads drop `provenance`, `source_url`, `website`, exact registry names and raw `lei`. New generic, category-level labels only via `vbie_core.public_source_labels()` + `public_evidence()` (e.g. "EU Government Procurement Records (Open Data)", "French Government Business Registry", "Global Company Identity Registry"). `compute_trust()` factor `detail` strings sanitised (no TED/GLEIF/trade.gov brands); stored trust recomputed for all 15,027 buyers. `/buyers/sources` returns generic categories (no url/attribution); `/meta` disclaimer names no registries. `intelligence` sends `lei_verified` bool, never the raw LEI.
- **Reveal Contact Details (subscriber-gated).** `POST /api/buyers/{geid}/contact` → active subscribers + admins get {email, phone, address, city, website, contact_name}; anonymous/non-subscribers → HTTP 402 (frontend routes to /pricing). Contact resolved SERVER-SIDE from source (TED buyer contact fields), cached to `entities.contact`, logged in `buyer_contact_reveals`. Frontend `ContactReveal` card on BuyerProfile; source URL never sent to browser. LEI relabelled to "Globally verified company identity ✓".
- **Contactable-only DB.** TED connector now fetches `organisation-email/tel/street/city/internet-address-buyer`; `run_ingestion` skips buyers without email/phone (`skipped_no_contact`). One-off `vbie_contacts.enrich_and_prune()` backfilled contact for existing buyers and HARD-DELETED 1,721 uncontactable ones (admin-edited preserved). Result: **15,028 active buyers, 100% with verified contact.** Admin endpoints: `POST /api/buyers/admin/contacts/enrich-prune`, `GET /api/buyers/admin/contacts/status`.
- New files: `vbie_contacts.py`. Test account: subscriber vaibhav@leadnation.app / Shiv@12345 (seeded active subscription). Command Center "Buyers" module is a teaser (no buyer list / no source leak) — nothing to hide there.



## BACKLOG (updated 2026-08-06)
- **CH Phase 1 bulk import (100K)** — WIRED & ready; run ONLY on user's explicit go-signal, then QA sign-off before scaling 100K→500K→1M→5M.
- **Razorpay subscription/reports go-live** — build complete & dormant; awaiting user's TEST keys to run end-to-end, then LIVE keys + webhook + redeploy.
- **Razorpay — professional services (GST/IEC etc.)** — SEPARATE keys (user will provide later). Must NOT reuse subscription/reports keys. Pro-services are enquiry-based today (no checkout); build a dedicated pro-services checkout only when those keys arrive.
- **New markets** — France SIRENE / Japan NTA / Australia ABN connectors to be built + enabled once API keys supplied (Norway + Czechia already live).


## VBIE PHASE 2.3 — PRODUCTION RECURRING INTELLIGENCE SERVICE (2026-08-04)
- **Permanent self-growing engine** (`vbie_scheduler.py`): DB-backed job store (`vbie_jobs`) — survives restarts, auto catch-up, retry queue, failure alerts, health heartbeat, per-source incremental checkpoints, source-specific schedules, job history. Replaces the old in-memory APScheduler that never reliably fired. Admin monitoring dashboard in BuyersManager (health, jobs, checkpoints, history, CH bulk). Endpoints: `/api/buyers/admin/engine/{health,history,checkpoints,jobs/{id}/run|toggle|interval}`.
- **New GREEN sources**: Norway Brønnøysund (NLOD) + Czechia ARES (open data) ENABLED (no key). Dormant pending keys: France SIRENE, Japan NTA, Australia ABN, Denmark CVR, Singapore ACRA, Finland PRH.
- **Companies House phased bulk** (100K→500K→1M→5M, `/api/buyers/admin/bulk/{phases,run-phase}`): streams to disk, SIC-46 (wholesale/import) filtered, QA snapshot per phase. USER initiates each phase after QA sign-off.
- **Auto-updating filters** verified: `/api/buyers/meta` live-distinct (Market/Sector/Corridor/Trust) now includes Norway + Czechia automatically.
- Status: engine healthy 8/8 jobs; 13,368 clean buyers; audit 0 quarantined. Verified iteration_39 (11/11 backend + frontend PASS).


## VBIE PHASE 2.2 — PRODUCTION READINESS AUDIT + ADMIN ANALYTICS (2026-08)
- **Production Readiness Audit** (`vbie_admin.production_audit`, `POST /api/buyers/admin/production-audit`, report `/app/memory/VBIE_PRODUCTION_AUDIT.md`): auto-quarantines any buyer that is a demo/sample, not from an approved connector, from a non-license-compliant source, missing provenance/trust-factors/country/sector/last_verified, a placeholder/invalid name, or a duplicate. Quarantined → `status='quarantined'` (excluded from public search/detail). Runs automatically after every ingestion. Result: **10,719 clean active buyers**, 3 junk quarantined ("N/A", "Test_Test", ".").
- Compliant-source allowlist (commercial reuse OK): EU TED (EU open-data reuse), Canadian Importers DB (OGL-Canada), SAM.gov (US public domain), UK Companies House (OGL v3).
- Added `last_verified` date on every buyer (backfilled + shown on profile).
- **Admin analytics** (`GET /api/buyers/admin/analytics` + `analytics.xlsx`): Today's Buyers, This Week, This Month, New Countries, New Industries, Top Products, Top Corridors, Top Sources, Top Countries — rendered in the admin console + downloadable Excel.

## BACKLOG (user-requested enhancements, not yet built)
- **P1 Unlock US & UK Buyers** — turn on SAM.gov + UK Companies House connectors once the free API keys are provided.
- **P1 Buyer Alerts** — let a subscriber save a product + market and get emailed when a matching new buyer is ingested.
- **P1 Corridor Signals Page** — country-by-country dashboard for Indian exporters showing who's buying their products abroad, with trend arrows.
- **P1 Turn On Emails** — add Resend API key so the "new buyers added" digest actually reaches user inboxes (currently MOCKED without the key).

## VBIE PHASE 2.1 — 10K SCALE + QA + ADMIN + BRAIN + NOTIFICATIONS (2026-08) — BUILT & TESTED (iteration_33, 100%, 16/16)
- **Scaled to 10,722 real buyers** (from 257) across 31 EU countries & 12+ sectors, via EU TED (24 CPV divisions × 16 pages × 365 days), bulk_write upserts. All sanctions-screened (trade.gov CSL, 53,796 denied parties). Daily scheduler 02:00 UTC.
- **Data Quality QA audit** — `GET /api/buyers/admin/qa` + `/app/memory/VBIE_QA_REPORT.md`. All 8 checks PASS: unique GEID, no duplicate entities, provenance present, source-registry compliance, explainable trust, country & sector classified, no demo data.
- **Admin buyer console** (`vbie_admin.py` + `BuyersManager.jsx`, admin tab "Verified Buyers"): list/search, edit (PATCH), soft/hard delete, bulk delete by source, **Excel (.xlsx) + PDF export**, ingestion trigger/status, admin bell notifications. **Admin edits/deletes PERSIST** — daily ingestion skips `admin_edited`/`admin_deleted` docs (admin always wins).
- **Brain integration** (`brain/router.py`): buyer-intent queries return `buyerAccess` gated by subscription (verified via Firebase token → `subscriptions`). Non-subscribers get a teaser (counts/markets/sectors) + subscribe CTA; **no contact details leaked**. Captures user buyer-search intent into `user_intent_signals`. Cache bypassed for buyer queries.
- **Notifications**: `notifications` collection. On ingestion with new buyers → user broadcast + admin notification + best-effort subscriber emails (`buyers_added` template; MOCKED unless RESEND_API_KEY set). User bell in Nav (`GET /api/notifications`, `/read`); admin bell in console.
- **Source transparency + warning**: buyer detail payload carries `primary_source` + `source_warning` ("verify directly; no consent/contact; business at your own risk") shown as an amber banner on `BuyerProfile`; `SourcesSection` on `/buyers` lists official sources + sanctions-screening count via `GET /api/buyers/sources`.
- **India Buyer Signals**: delivered via the corridor filter (IN-DE, IN-FR…) on `/buyers` + Command Center; `vbie_market_stats` holds UN Comtrade India-export corridor context.
- Pending user: SAM.gov + UK Companies House free API keys (connectors wired, currently return 0). CID host-blocked from this environment.
- Known minor (non-blocking, from iteration_33): admin PATCH returns changed field-name list (UI reloads anyway); admin search doesn't match on GEID; a transient 502 possible on `/meta` during heavy ingestion.

## VBIE PHASE 2 — LIVE REAL BUYER INGESTION + PAYWALL (2026-08) — BUILT & TESTED (iteration_32, 100%)
**Replaced the 12 illustrative demo buyers with REAL, daily-ingested buyer intelligence from official government sources.** Single-writer rule enforced: ALL buyer/entity writes happen in the Website backend (`vbie_connectors.py`); DO backend never writes the buyer graph. APIs-first, legally compliant — NO scraping of prohibited/tos-gated sites.
- **New `/app/backend/vbie_connectors.py`** — connector framework + orchestrator + daily APScheduler (02:00 UTC). Connectors:
  - **EU TED** (`api.ted.europa.eu/v3/notices/search`, no key) — PRIMARY live named-buyer source: real EU public-sector buyers actively procuring goods, across 8 CPV divisions → 7 LeadNation sectors, 27 EU countries. Open reuse licence.
  - **trade.gov CSL** (bulk JSON, no key) — MANDATORY sanctions/denied-party hard gate on EVERY buyer (~53,796 names; blocks matches before surfacing). Cached ~20h.
  - **UN Comtrade preview** (no key) — India export-corridor market context → `vbie_market_stats`.
  - **Canadian Importers Database** (open data CSV) — real named importers by HS; best-effort (currently host-blocked → returns 0, skips gracefully).
  - **SAM.gov** (needs free `SAM_GOV_API_KEY`) + **UK Companies House** (needs free `COMPANIES_HOUSE_API_KEY`) — wired, skipped until keys provided. Optional `COMTRADE_API_KEY`.
  - `run_ingestion()`: fetch → sanctions-screen → deterministic-GEID upsert into `entities` (`sample:false`, `source_verified:true`, `created_by:'vbie-connector:<src>'`) → delete leftover demo `sample:true` buyers once real data exists → log to `vbie_ingest_runs`. First startup: 257 buyers, screened_out=1, samples_removed=12.
- **`vbie.py` changes:** `seed_vbie()` now seeds ONLY the source registry (no fake buyers). **PAYWALL:** `_entitlement()` — full buyer profile requires signed-in Firebase user + active `subscriptions` doc (admins bypass). `GET /buyers/{geid}` returns a LOCKED teaser (name/country/sector/trust band only; website+provenance hidden) with `locked:true, lock_reason:'login'|'plan'` when not entitled; `GET /buyers/{geid}/evidence` → 402 when not entitled. New: `GET /buyers/sources` (public transparency: registry + sanctions + last run), `POST /buyers/ingest/run` (admin), `GET /buyers/ingest/status` (admin). `/buyers/search`, `/meta`, `/claim` stay public (SEO teaser + lead-gen).
- **Frontend:** Nav gains prominent **"Verified Buyers"** primary entry (`/buyers`). Home gains `home-verified-buyers` teaser section + `home-buyers-cta`. `BuyerProfile.jsx` renders a **PaywallGate** (blurred teaser + Sign-in/View-plans CTAs) when `locked`. `BuyerIntelligence.jsx` hero copy updated to reflect real official-source data.
- **App sync:** the mobile app consumes the SAME shared `/api/buyers/*` endpoints (shared Mongo) — no Firestore copy. Verified iteration_32: backend 14/14, frontend all flows, admin gating, sanctions gate, paywall (locked path). Entitled/admin UI path can only be verified via backend fixtures (Firebase UI login is CORS-blocked in preview). Pending user: SAM.gov + Companies House free API keys to light up US/UK registry connectors.

## VBIE PHASE 1 — Verified Buyer Intelligence Engine (2026-06) — SUPERSEDED BY PHASE 2
**Architecture LOCKED & user-approved:** the **Website/Command Center backend is the single Global Trade Intelligence Server** — VBIE (buyer/entity graph, provenance, sources, trust) is owned & served ONLY here, consumed by web + app + future clients via shared `/api/*`. The **DO backend stays identity-only** (users, customer_id allocation, onboarding, `company_profiles`, `members_bridge`). Refinement: the canonical **buyer/supplier entity graph is written ONLY by the Website backend**; DO may read a GEID for member binding but never writes the buyer graph (avoids two writers). Both share the same Atlas `leadnation` DB; VBIE writes only `entity_type='buyer'` docs (additive, `created_by='vbie-seed'`).
- **Backend `/app/backend/vbie.py`** (router prefix `/buyers`): `GET /meta` (facets+disclaimer), `GET /search` (filters: q [regex-escaped], country, sector, corridor, hs, trust_min; sorted by trust desc; paginated), `GET /{geid}` (Buyer Card, follows merges), `GET /{geid}/evidence` (provenance), `POST /{geid}/claim` (request-introduction → `buyer_claims` + mirrors to `leads` CMS). Collections: `entities` (buyer docs), `vbie_sources` (10-source registry), `buyer_claims`. Deterministic **Trust v0** (source-reliability 70% base + verification signals + freshness → 0-100 + band Verified/Trusted/Emerging/Unverified, explainable factors). GEID `LN-buyer-<26 Crockford>` (deterministic from slug → idempotent reseed). Seeded on startup + indexes in `server.py`.
- **Seed = 12 illustrative buyers** across US/UK/DE/AE/AU × 6 sectors, each `sample:true` with honest source-typed provenance (UN Comtrade, trade.gov CSL, UK Companies House, SAM.gov, EU TED, VIES, ABR, etc.). NO fabricated shipment figures against named firms; UI shows an illustrative-data disclaimer. Real official/free connectors are the next slice.
- **Frontend:** `lib/vbieApi.js`, `components/BuyerCard.jsx` (+ `TrustBadge`), `pages/BuyerIntelligence.jsx` (route `/buyers` — hero, filter sidebar, reactive buyer grid), `pages/BuyerProfile.jsx` (route `/buyers/:geid` — trust breakdown, products/HS/corridors, Source Evidence list, Request-Introduction/claim modal). Routes wired in `App.js`.
- Verified iteration_31: backend 11/11 pytest 100%, frontend all flows 100% (12 cards render, filters+search reactive, profile trust+evidence, claim modal success). Only cosmetic note: site-wide cookie banner overlaps profile bottom at 1080p (pre-existing).


## APP-TEAM DIRECTIVE (2026-06) — Phase C APPROVED · Minimal Phase B · Guarded Phase D · STOP boundary
Independently reviewed `shaili-trademate-app-main (2).zip` (`backend/server.py`) line-by-line. Decisions (permanent, future-ready) captured in `/app/memory/APP_TEAM_PROMPT_PHASE_C_APPROVAL_AND_PHASE_B.md`:
- **Phase C (GEID entity model) = APPROVED.** `entities`(GEID, immutable `_id`, `LN-<type>-<ULID>`) is sole identity; `company_profiles` = editable-only w/ geid FK; `members_bridge{uid,customer_id,geid}` unique uid+cid, non-unique geid; merge follows pointers + moves bridges/profiles to survivor; startup indexes correct; users/_counters untouched. Phase A polish confirmed (canonical `mobile` in admin `$or`, `uniq_mobile` sparse-unique index). **2 required hardenings before Phase B:** (1) admin/service-gate canonical GEID minting for buyer/supplier/manufacturer/agency; allow only 1 self-minted member_company/prospect per user (reject dup, return existing GEID); (2) merge idempotency + cycle guard.
- **Phase B (networking→Mongo) = MINIMAL.** Mongo networking/chat BACKEND ALREADY EXISTS (`v1b_router`: /connections/*, /chats/*, /chats/{id}/messages; `v1_connections`/`user_connections`). Only work = repoint mobile `frontend/services/networkDB.ts` off Firestore (PROFILES/REQUESTS/CONNECTIONS + onSnapshot) onto those Mongo endpoints; replace onSnapshot with polling (React Query refetchInterval); Firestore count→backfill-if-any→retire. DEFER WebSocket/Atlas change-streams (keep messages schema realtime-ready: `(chat_id, created_at)` index + monotonic `seq`, single service module).
- **Phase D = GUARDED UI ONLY.** Optional country-code+E.164 phone at signup; login "Mobile" tab gated by `EXPO_PUBLIC_ENABLE_PHONE_LOGIN` (default false); NO live SMS until Firebase Blaze.
- **STOP boundary:** after A(done)+C(approved+2 hardenings)+minimal B+guarded D → app team stops auth/architecture work; next = jointly-approved VBIE implementation via Research→Design→Review→Approval gate. App team must runtime-test in its own env (not just code review).


## Implemented (2026-06 forked session) — Guarded Mobile-Number Login + VBIE R&D program
- **IDENTITY & AUTH ARCHITECTURE = FROZEN (2026-06).** Signup now collects mobile as an OPTIONAL field with a country flag + dial-code selector (India 🇮🇳 +91 default), stored E.164-normalized in the shared `users` record (sent as `mobile` + `mobile_number`; country derived from selector) + note "…faster login and account recovery when Phone Login becomes available." (`Auth.jsx` + new `lib/countryCodes.js`). Verified iteration_30 (frontend 100%).
- **Admin Users view DONE & VERIFIED (iteration_30):** AdminDashboard "Users" tab (`RegisteredUsers`) reads DO `GET /admin_v2/users` via `authApi` — website + app admins see every user's Customer ID/name/email/mobile/role/country/status (read-only; hard-delete stays on DO super-admin). No duplicate user store.
- **Guarded Phone (mobile-number) login DONE & VERIFIED (iteration_29, frontend 100%):** `AuthContext.jsx` adds `startPhoneLogin/confirmPhoneOtp` + `phoneLoginEnabled` flag = `REACT_APP_ENABLE_PHONE_LOGIN==="true"` (default OFF/guarded until Firebase Blaze). `Auth.jsx` Login now has "Email / Customer ID" + "Mobile number" tabs; with flag OFF the mobile tab shows a "launching soon" guarded note (no phone input, SDK never called). Google/Email/Customer-ID login UNCHANGED. reCAPTCHA cleared on logout. Website remains a PURE CLIENT — no backend/identity-ownership change. To activate post-Blaze: set `REACT_APP_ENABLE_PHONE_LOGIN=true` + restart frontend; app team must add DO `/auth/resolve-mobile` + store `users.mobile` (E.164).
- **CANONICAL identity standard:** `/app/memory/LEADNATION_UNIFIED_IDENTITY_ARCHITECTURE_STANDARD_v1.md` — ONE Firebase (trademate-new) + ONE Atlas (leadnation); DO backend owns identity + the SINGLE 5-digit customer_id allocator (`_counters`); website is pure client. `entities`(GEID) = SOLE company identity layer; `company_profiles` = editable profile data ONLY (references GEID, never identity); `members_bridge{uid,customer_id,geid}` is the only join. Networking → Mongo-only (retire Firestore `user_connections`).
- **VBIE (Verified Buyer Intelligence Engine) R&D — design only, NO production code yet:** full 8-phase blueprint under `/app/memory/research/` + `/app/memory/research/platform/` (Phases 1–5 designed & approved): source registry (`sources_seed.json`, 50 sources), connector/crawler framework, entity-centric data model w/ GEID + knowledge-graph readiness, 5-Brain modularization, Networking↔VBIE unification. Provider comparison (Volza/ImportGenius/Panjiva/Datamyne). Discipline: Research→Design→Review→Approval before any build.


## 🔒 RELEASE FREEZE (2026-07-05) — Deployment Prep + Mobile Handoff
Feature development STOPPED. Baseline = **Volume 1 + Volume 2 Phase 2A** → first production release, tag `v1.0-leadnation-command-center-production-ready`. Do NOT start Volume 2B/2C/2D, Volume 3 or 4 until website + mobile app are live.
- **Cookie Consent (GDPR/CCPA) DONE:** `CookieConsent.jsx` + consent-aware `analytics.js` — Accept All / Reject Non-Essential / Manage Preferences; Essential always-on, Analytics (GA4/GTM/Clarity) + Marketing (Meta) opt-in; analytics load ONLY after consent; stored in localStorage; footer "Cookie Preferences" to change; first-party anonymous `/api/track` retained (PII-scrubbed). Verified E2E.
- **Analytics activation DONE:** env-driven, consent-gated, standard EVENTS wired, privacy scrubber, first-party pipeline → `db.events` (admin-dashboard-ready). See `ANALYTICS.md`.
- **App build prompt:** `/app/memory/APP_BUILD_PROMPT.md` — paste-ready Emergent prompt to build the RN/Expo Command Center connected to the same backend/Firebase/Mongo (thin client). Full contracts in `TRADE_COMMAND_CENTER_APP_INTEGRATION_GUIDE.md`.
- Delivered earlier: mobile integration guide, `PRODUCTION_READINESS.md`, 5 legal pages, MongoDB indexes.

## Implemented (2026-07-05) — VOLUME 2 PHASE 2A: Simulation & Decision Engine
Layered architecture (permanent): **Trade Project → Reactive Graph → Simulation Engine → Decision Engine → LeadNation Brain → Report**. Deterministic maths run on the backend; the Brain only explains/interprets (never fabricates numbers). Verified iteration_24 (backend 19/19 pytest; UI module renders; Brain-crash bug FIXED).
- **Separate collections (permanent):** `trade_project_scenarios`, `trade_project_events`, `trade_project_brain_history` (+ existing `trade_projects`). Scenarios are NOT embedded in the project doc.
- **Live Data Adapter Framework (`adapters.py`):** one standard interface (`Adapter.fetch → AdapterResult{value,source,sourceTier,confidence,aiEstimated,reason,assumptions}`); tiers gov>official>live_commercial>knowledge_base>historical>ai_estimate. Wired adapters: duty(WITS·gov), fx(official), trade_stats(OEC), incentives(DGFT/CBIC·gov), freight(ai_estimate). Future feeds `register()` and plug in. `GET /api/adapters`, `POST /api/adapters/run`.
- **Simulation Engine + Scenario Builder (`simulation.py`):** `POST /api/simulation/twin` (Digital Twin what-if, instant recompute, no save); scenario CRUD `/api/simulation/scenarios` (+duplicate, merge, archive, delete, versioning); `/api/simulation/compare` (rows + winners per metric). Each scenario stores inputs/outputs/scores/decision/confidence/parentId/version.
- **Trade Score Engine (`scores.py`):** 8 explainable deterministic scores (profitability, risk, compliance, competition, market, buyer, supplier, overall) — each with value/color/factors/explanation.
- **Decision Engine (`decision_engine.py`):** `build_decision` consolidates outputs into structured decision objects (6 domains) + recommendedActions + verdict + confidence. `POST /api/decision`. `POST /api/decision/recommendations` → Brain reasons over STRUCTURED objects (+ deterministic fallback so output is never empty).
- **Universal Audit Trail (`events.py`):** `trade_project_events` logs project_created/scenario_*/decision_computed/brain_recommendation/quote_generated/buyer|supplier|currency|route_changed etc. `GET /api/events?projectId=`.
- **Frontend Simulation module** (Command Center tab `cc-mod-simulation`): Trade Score Engine (expandable factor explanations), Decision Engine (prioritised actions + Brain recommendations), Scenario Builder with Digital Twin inline editing (margin/freight/insurance/incoterm), compare table + recharts bar chart + winners. Renders whenever product/HS present.
- **PDF integration (Volume 2):** `CommandCenterReport.jsx` self-fetches /decision + /simulation/compare and adds Trade Scores, Scenario Comparison, Decision recommendations, Report ID + QR code, generation date.
- Bug FIXED: Brain provider crashed on list `data` payloads (providers.py now tolerates list/dict; decision_engine passes dict-shaped data).

## Implemented (2026-07-01 PM) — Pricing Engine + Subscriptions + India Globe fix
- **P0 FIXED — 3D Trade Globe India map:** now overlays the official India political boundary (includes J&K & Ladakh, extent to lat ~37°) from a locally-served TopoJSON (`/geo/india-states.json`, merged via topojson-client). World-atlas India (truncated) is filtered out; India is highlighted in violet. Verified visually via screenshot. (`TradeGlobe.jsx`)
- **Centralized Pricing Engine (`backend/pricing.py`)** — SINGLE SOURCE OF TRUTH for all prices. Mongo `pricing_config` doc; endpoints `/pricing/config` (public, per-region), `/pricing/track` + `/pricing/lead` (funnel + email capture, guest), `/pricing/admin` GET+PUT (admin), `/pricing/admin/analytics`. Helpers `resolve()`, `gateway_for()`, `get_config()`. **NOTHING is hardcoded downstream** — `monetize.py` now reads every price from the engine (download / monthly / annual, IN & INTL). Verified iteration_23 (11/11 backend 100%).
- **Admin Pricing tab (`PricingManager.jsx`)** — Admin edits India+International prices for all plans, plan labels/taglines/active, gateway enable toggles (Stripe/Razorpay + future), settings (freeFirstDownload, emailCaptureBeforePaywall, Most Popular plan) + live paywall funnel analytics. New tab in `/admin-cms`.
- **Public Pricing page (`/pricing`, `Pricing.jsx`)** — region toggle (IN₹/INTL$), 3 plan cards, Most Popular badge, annual-savings %, feature comparison table, conversion tracking. Added to top nav.
- **Subscription system:** monthly (30d) + annual (365d) passes via Stripe; `create_checkout` supports kind download|monthly|annual|subscription; sub duration from `SUB_DAYS`.
- **Paywall UX upgrade (CommandCenter Reports + AccountPage Billing):** email capture before paywall, annual+monthly plan options with Most Popular badge, dynamic prices, "just this once" pay-per-report link, conversion tracking events. AccountPage billing shows dynamic monthly/annual cards.

## PERMANENT ARCHITECTURAL RULE — Customer IDs (option c, user-mandated)
- The website NEVER generates/modifies/reserves/enforces Customer IDs. Allocation is owned SOLELY by the shared LeadNation DigitalOcean backend (`/api/onboarding/register`, `_counters`).
- Backend rule (to be enforced on DO backend, OUT OF THIS CODEBASE'S REACH): IDs are numeric, exactly 5 digits (00002–99999), `00001` reserved for Super Admin, immutable, unique across web+mobile.
- Website responsibility: only VALIDATE the returned ID matches `^\d{5}$` before display; never create/modify. (⚠️ DO-backend change is a user/backend-team action; front/local backend cannot alter it.)

## Implemented (2026-07-01 AM) — Monetization + Account + Costing UX + dropdown fix
- **Dropdown white-bg bug FIXED** (index.css `select option` dark styling) + **Product→HSN autocomplete** on Start screen (verified iteration_21, 100%).
- **Costing UX:** current-stage indicator ("Stage X of 9"), sidebar tooltips, ⌘K button renamed **"Menu"**, **(i) info tooltips** on all cost fields, **Unit dropdown** (MT/KG/Ton/Container…), **Destination Port dropdown** (per country), 11 Incoterms + info, **Autofill with Brain** button (verified iteration_20, 100%).
- **Monetization (`monetize.py`):** Stripe pay-per-download (first download FREE, then ₹25 IN / $1 INTL) + monthly unlimited pass; `/payments/checkout|status|pricing`, `/webhook/stripe`, `/downloads/check|record` (first-free logic), GST-style invoices, referral codes. Owner = Firebase UID or guest Trade-Session. **Razorpay slot ready (RAZORPAY_KEY_ID env) — keys pending from user (2-3 days).** Verified iteration_22 backend 100% (8/8).
- **Account page (`AccountPage.jsx`, /account):** Instagram-style header (avatar, name, **role badge**, **country+flag**, **User ID**, mobile, email), stats, tabs: Downloads / Projects / Saved Buyers / Invoices / Billing (monthly pass) / Referral. Profile edit (role/country/mobile) with local override on DO profile. Post-Stripe-redirect auto-completes the paid download + prints PDF. Verified iteration_22 (account 100%).
- **Paywall gate** on Command Center Export PDF: not-signed-in → "Sign in to download" modal; signed-in → free/pass → download, else pay modal (₹25/$1 or monthly pass). Verified working via reproduction (login-gated E2E to be validated on production — login CORS-blocked in preview).
- **Admin:** `/account/admin/users` + `/account/admin/{owner}` (require_admin) — revenue, downloads, per-user view.
- Known cosmetic: a React dev-only "span in option" console warning (no functional impact).

## Monetization plan (agreed)
- Free: build quotes/projects. Paid: PDF download — first free, then ₹25 (IN, Razorpay) / $1 (INTL, Stripe), or monthly unlimited (₹499 / $9). Geo by profile country. Referral + credit-pack/subscription upsell.

## Backlog / next
- **Razorpay wiring** (awaiting user keys) — INR ₹25 + ₹499/mo via Razorpay; Stripe handles INTL.
- Stripe webhook secret + production verification of login-gated download & account sync.
- Vol 2 (Digital Twin), Vol 3 (live data adapters, proactive alerts, Knowledge-Quality), Vol 4 (collaboration, white-label PDF, ERP).


- New full-screen workspace at **`/command-center`** (sidebar · center · right Brain panel). Home CTA + customs tab now point here.
- **Trade Projects** (`backend/projects.py`, `trade_projects` collection): create/autosave/load/recent/pin/duplicate/templates/delete; **guest (anonymous UUID) ↔ Firebase UID ownership with auto-merge on login** (`/projects/merge`). Production-ready + testable in preview without login.
- **Universal Project Context** (`frontend/src/lib/ProjectContext.jsx`): one state spine, **reactive computation graph** (change any input → quote/duty/tax/currency/markets/health/Brain recompute, no re-click), `patchCosts` (stale-closure-safe nested edits), persist-merge preserving freshest lastQuote/costs.
- **Modules**: Overview (Executive Dashboard + Project Summary + 7 health score rings + alerts + timeline), Trade Costing (reactive FOB→CIF waterfall + Explain on every KPI), Market Research (buyer comparison), Compliance (per-country duty+docs+Brain brief), Documents (checklist), Routes, Risk (score bars), Buyers/Suppliers (Brain + app CTA), Reports (PDF export + version history), Brain (project-aware chat), Settings (assumptions panel + project fields).
- **Workflow engine** (9 stages, clickable stepper, Brain-aware), **Activity Timeline**, **Version History**, **Assumptions Panel**, **Data-Source badges** (Govt/Live/Brain/Manual/Historical/Estimate), **Command Palette (⌘K)**, **Explain Everything** (`/command-center/explain`).
- **PDF export** (`CommandCenterReport.jsx`): branded Quote + cost waterfall + buyer comparison + **per-destination-country compliance report**.
- Backend: `/command-center/quote` (parallelized 8-market comparison), `/explain`, `/compliance`, `/markets`; `duty_engine` WITS year-window narrowed to 6 for latency. Client timeout raised to 90s for cold lanes.
- Docs: `TRADE_COMMAND_CENTER_VOL1.md` (blueprint) + `TRADE_COMMAND_CENTER_VOL1_COMPLETION.md` (as-built report, 10 diagrams, checklist, Volumes 2–4 roadmap).
- **Permanent rule adopted:** every feature must belong to / enhance a Trade Project. **3-Click Rule** for major tasks.
- Verified: test_reports/iteration_19.json — 100% backend (18/18), 100% frontend functional. Minor (fixed): strokeLinecap warning, sort tiebreaker. Known: cold first-run lane ~15-25s (cached after); compliance first-load shows spinner.

## Earlier (2026-06-30) — Trade Command Center calculator (iteration_18, 100% pass)
- Renamed Compile Data → Trade Command Center tab; world-class FOB/CIF/landed calculator; buyer-landed-cost comparison; dual+global currency; AI advisor; Home section before Services.

## Backlog → mapped to Volumes 2–4 (see completion report)
- **Vol 2** Digital Twin scenario simulation (consumes Assumptions Panel) + confidence scoring + math models.
- **Vol 3** Live data adapters (freight/buyer/supplier/govt/customs/shipping/banking APIs), proactive Brain alerts, Brain co-pilot site-wide, Knowledge-Quality confidence engine.
- **Vol 4** Collaboration (teams/comments/approvals), white-label Quote PDF + My Reports + shareable links, ERP integration, security/deploy hardening.
- Pending/partial: real Buyers/Suppliers datasets, per-value confidence+timestamp, live shipment tracker, cold-latency bulk-tariff store.


- Delivered **Volume 1 — Master Product Blueprint** (`/app/memory/TRADE_COMMAND_CENTER_VOL1.md`): full product architecture (vision, philosophy, user journeys, dashboard, workspaces, Brain integration, knowledge flow, Trade Projects, Digital Twin, system + dependency diagrams, ImpexQ competitor analysis, 2026–2035 roadmap). All future features reference this.
- **Backend `costing_engine.py`** (`/api/command-center/*`), registered in server.py:
  - `POST /quote` — 100% deterministic, instant: Ex-Works→FOB→CIF 9-row waterfall, destination duty (WITS) + VAT (`VAT_BY_CODE`, ~55 countries) + landed cost, margin→selling price, **buyer-landed-cost comparison** across up to 8 markets (sorted ascending), **dual + global + exporter-local currency** conversion (live FX), export incentives (RoDTEP/GST/Drawback/Adv. Auth for India origin), indicative routes/transit. Verified FOB=80500/CIF=85600 for HS 100630 India→Germany ×1000.
  - `POST /insights` — separate call so numbers render first; LeadNation Brain (live `gpt-5.4-mini`) returns grounded markdown advisor (insights, best market, savings, risks). Verified live + grounded.
  - `GET /markets` — 146 countries.
- **Frontend** `CustomsCompliance.jsx` → `CommandCenterTool`: tab renamed "Compile Data" → **"Trade Command Center"** (first tab). Lane setup (product autocomplete, export/import, qty+unit, **transaction currency + user-picked global currency**, margin), editable BLANK cost build-up with **live FOB/CIF preview as you type**, KPI cards (3 currencies each), cost waterfall, duty/tax panel, ranked buyer-comparison table (★ best), multi-currency quote, incentives+routes, **AI Trade Advisor** (Brain, progressive), Print/Save quote (PDF via `#cc-print` print CSS), Ask the Brain.
- **Home**: new `home-command-center` section BEFORE Services, tagline "The World's First AI-Powered Global Trade Operating System." + CTA to /customs-compliance.
- Hero/SEO of /customs-compliance updated to Command Center framing.
- Verified: test_reports/iteration_18.json — 100% backend (11/11) + 100% frontend + 4 regression tabs, zero issues.
- User choices honoured: build-all (1a), user picks global currency (2c), blank cost fields (3b). Latency: deterministic instant + Brain streams in via separate /insights call.

## Backlog directly from Vol 1 (next priorities)
- **P1** Trade Projects: save/load/duplicate stateful projects to the account; templates; shareable client links.
- **P1** Quote PDF polish (branded white-theme proposal) + My Reports history.
- **P1** Digital Twin scenario simulation (currency/freight/duty/delay deltas → live profit).
- **P1** Proactive Brain alerts (duty/FX/freight/policy thresholds).
- **P1** Increase Brain involvement across other tools (context co-pilot) + Knowledge Quality (live vs estimated) + feedback → Admin Knowledge Gaps.
- **P2** Live data adapters (real freight indices, premium buyer/supplier data, govt APIs); Vols 2–4.
- **P1** Legal pages; Analytics activation (GA4/GTM/Clarity/Meta env scaffolding present).


## Implemented (2026-06-30) — P1: Dual currency + Premium Trade Intelligence Report
- [x] **Dual currency (Compile Data)**: backend auto-detects the exporter country's local currency (`duty_engine.CURRENCY_BY_CODE`) + user's transaction currency; `/api/compile/report` returns live FX + landed cost in USD, exporter currency AND transaction currency. UI panel shows all three. (cache bumped to `v2:`). Verified: India→INR, USA→USD.
- [x] **Premium Trade Intelligence Report** (`frontend/src/components/TradeIntelReport.jsx`): branded, white-theme, 12-section printable report (cover, snapshot KPIs, executive brief, HS classification, global stats + trend bars, top importers/exporters, duty & benefits, tariff comparison, dual-currency FX, landed cost, logistics, next steps, sources+disclaimer). Client-side **Print / Save as PDF** via `@media print` in index.css (renders only `#trade-report-print`). Overlays use React portals to escape transformed ancestors.
- [x] **Lead Capture gate**: signed-out users must submit Name/Email/Company/Country (+optional phone) → `POST /api/leads` (source `trade-intelligence-report`, report context in message) → saved to Lead CMS, then report opens. Signed-in users skip the gate. Verified end-to-end in-browser + lead persisted to CMS.
- NOTE: HSN Google-style autocomplete was already present in Compile/Duty/TradeStats tabs (pre-existing).
- ⏳ Pending user input: increase Brain involvement + add more to Brain replies (user reported Brain latency; will share specifics).

## Implemented (2026-06-30) — Auth FINALIZED: website is a pure client of the deployed shared backend (NO proxy, NO local DB)
- [x] Frontend now calls `https://leadnation-lfrhs.ondigitalocean.app/api` DIRECTLY for ALL identity (env `REACT_APP_AUTH_API_BASE`, never hardcoded). New `src/lib/authApi.js` (Firebase Bearer interceptor); `AuthContext` repointed.
- [x] Endpoints wired & E2E-verified server-side: resolve-customer-id → Firebase login → `GET /api/v1/profiles/{uid}` (current-user source; DO has NO `/auth/me`) → idempotent `onboarding/register` → admin `admin_v2/users`. OTP via `send-otp`/`verify-otp` (body `{type:"email",value,otp}`; DO has NO `request-otp`).
- [x] Deleted local `accounts.py` — website does ZERO identity DB writes. Local backend retained ONLY for website content (Brain, trade-intel, duty, compile, customs, CMS). `core.require_admin` only READS shared `users.role`.
- ⚠️ CORS: production `leadnation.app` allowed (login works in prod); **Emergent preview origin still CORS-blocked (400)** → backend owner must whitelist `global-trade-hub-176.preview.emergentagent.com` to test login in-preview. Integration verified via curl.


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

## Fixed (2026-06-29) — Auth bug fixes (email verification + Google)
- [x] **Email verification via TEST OTP**: `/api/auth/request-otp` + `/api/auth/verify-otp` (code `123456`, env `TEST_OTP`) marks Firebase `email_verified` + Mongo `users.is_email_verified`. Account page shows a verify card (enter 123456 → flips to Verified); frontend force-refreshes the ID token. Verified for account 00009. (Swap TEST_OTP for a real OTP/SMS provider later.)
- [x] **Google sign-in graceful failure**: `googleErr()` maps `auth/unauthorized-domain` etc. to a friendly message instead of crashing. ROOT CAUSE: the Emergent preview domain is not in Firebase Authorized Domains — Google works on leadnation.app/Vercel (already whitelisted). To test Google in preview, add `global-trade-hub-176.preview.emergentagent.com` in Firebase Console → Auth → Settings → Authorized domains.
- Verified: test_reports/iteration_17.json — 3/3 backend + UI flows PASS. Throwaway users cleaned (DB = 00001 + 00009).


## Implemented (2026-06-29) — SHARED LOGIN PHASE (Firebase + Atlas, app-interoperable)
- [x] **ONE identity, ONE database** with the mobile app: switched backend to shared **MongoDB Atlas DB `leadnation`** + shared **Firebase project `trademate-new`** (Email/Password + Google). Passwords live ONLY in Firebase.
- [x] `firebase_auth.py` — inits Firebase Admin from `FIREBASE_SERVICE_ACCOUNT_B64`, verifies `Authorization: Bearer <firebaseIdToken>` on protected routes.
- [x] `accounts.py` — `/api/auth/resolve-customer-id`, `/api/onboarding/register` (idempotent Customer-ID allocation via shared `_counters`, one uid→one customer_id), `/api/auth/me`, `/api/admin_v2/users`, `DELETE /api/admin_v2/users/{cid}/hard-delete` (purges Mongo + Firebase Auth + Firestore; protects 00001 & self). users/profiles schema matches the app exactly (additive).
- [x] Admin migrated from JWT/bcrypt → **shared Firebase admin** (`admin@leadnation.app` / `00001` / role:admin). `core.require_admin` now verifies Firebase token + `users.role=='admin'` (legacy X-Admin-Token kept as emergency fallback only). Removed the separate `admin_users` store.
- [x] Frontend: `firebase.js` + `AuthContext` (email/pw, Google, Customer-ID login, password reset, email verify, session persistence) + axios Bearer interceptor. New `/login`, `/signup` (with business role), `/forgot-password`, `/account` pages. Nav shows Sign in/Account. Admin login at `/admin-login` now uses Firebase.
- Verified end-to-end against PRODUCTION shared Firebase+Atlas: test_reports/iteration_16.json — 9/9 backend + all UI flows PASS (resolve, token gate, admin list, register idempotency, hard-delete + 00001 protection). Throwaway test users cleaned up (DB back to 1 user = admin).
- ⏳ Firebase authorized domains already include leadnation.app/Vercel; add any NEW website domain in Firebase Console → Auth → Settings → Authorized domains.

## Deferred (next phases, per user's production-readiness spec)
- Compile Data → premium 19-section Trade Intelligence Report; PDF download + Print (client-side) + Lead Capture gate.
- My Reports history + shareable public/private links (uses the now-live accounts).
- Legal pages (Privacy/Terms/Cookie/Disclaimer/Refund); Analytics activation (env scaffolding present: GA4/GTM/Clarity/Meta).
- Brain rich feedback → Admin "Knowledge Gaps"; Knowledge-quality indicators (engines used, live vs estimated).
- Security review, SEO/perf/a11y reports, Integration Matrix, Go-Live checklist.


## Implemented (2026-06-29) — Brain goes GLOBAL + Compile Data + Phase C
- [x] **BUG FIX — Brain global & non-repetitive**: rewrote `brain/providers.py` SYSTEM prompt (global, answer-the-specific-question, ground numbers in live engines, use own expertise for any country's compliance, never default to India). Made `trade_news/market_intelligence/logistics/policy/tariff` engines global & dynamic (removed hardcoded India boilerplate like "$450B exports", "Mundra"). Tightened `router.py` engine selection (cap 5, dropped legacy `tariff`/`network`/`marketplace` from auto-select) and added global country detection (scans `duty_engine.COUNTRIES`). Verified: 3 distinct queries → 3 distinct, country-specific, non-India answers.
- [x] **Compile Data master tab** (`compile_engine.py`, `/api/compile/report`): one-click brief for product + export country + import country + currency → aggregates trade stats, duty & benefits, tariff comparison across 6 markets, live FX, sample landed-cost, freight, + a Brain-written **Executive Brief** (LLM). New default tab `CompileDataTool` on `/customs-compliance` with `MarkdownLite` renderer.
- [x] **Phase C — CBIC notified customs FX**: `/api/customs/cbic-fx` returns India CBIC notified import/export rates + notifiedDate. (Data layer live; calculator-UI wiring is a small follow-up.)
- Verified: test_reports/iteration_15.json — 11/11 backend + all UI flows PASS.


## Implemented (2026-06-29) — Phase B: Duty & Benefits engine (real, weekly-refreshed)
- [x] New backend `duty_engine.py`: unified **global import tariffs** (World Bank WITS / UNCTAD TRAINS, reporter=destination × partner=origin × HS6), **India duty breakdown** (BCD from WITS + IGST slab + 10% SWS), and **DGFT RoDTEP** export benefit (chapter-level, Mongo `rodtep_rates`). Endpoints: `/api/duty/countries`, `/duty/meta`, `/duty/lookup?hs=&origin=&destination=`, POST `/duty/refresh` (admin-gated).
- [x] Origin↔destination country filter (56 major countries). Real verified data: USA→India coffee 100% MFN; USA→Germany cars 10%; India→Germany coffee RoDTEP 1.4%.
- [x] **Weekly APScheduler** (7-day) auto-refresh clears tariff cache + restamps `duty_meta.lastRefresh`; "updated on" shown to users; manual **"Refresh data now"** button in Admin Control Center.
- [x] Brain engine `duty_benefits` wired (keywords duty/tariff/rodtep + country pairs) — Brain answers duty questions with real numbers.
- [x] Frontend: new **"Duty & Benefits"** tab on `/customs-compliance` (DutyBenefitsTool) + admin "Trade & Duty Data" refresh card.
- Verified: test_reports/iteration_14.json — 9/9 backend + all UI + admin refresh + Brain PASS.


## Implemented (2026-06-29) — Phase A: Live Global Trade Intelligence
- [x] New backend engine `trade_intel.py`: REAL global trade stats by HS code. Two sources, freshest wins: **OEC World API** (free, no key, always on) + **UN Comtrade** (activates when `COMTRADE_API_KEY` env set). Endpoints: `/api/trade-intel/status`, `/hs-search?q=`, `/stats?hs=`. HS6 directory (5606 codes) built from OEC and cached in Mongo `trade_hs_map`. Results cached in `trade_cache` (14-day TTL ≈ bi-weekly).
- [x] Returns: total world trade value, top importing & exporting countries (value + share), multi-year trend, source + year + freshness. GLOBAL (not India-only).
- [x] Brain engine `trade_statistics` wired into `brain/engines.py` + `router.py` selection (keywords + HS code presence). Brain answers trade-stat questions with real numbers.
- [x] Frontend: new **"Trade Statistics"** tab on `/customs-compliance` (TradeStatsTool) — product/HS search w/ autocomplete, world value, importer/exporter bars, trend chart, Ask-the-Brain CTA. Customs hero/SEO updated to global framing.
- Verified: test_reports/iteration_13.json — 8/8 backend + all UI flows PASS (live OEC data).
- ⏳ Pending: user to add UN Comtrade API key (`COMTRADE_API_KEY` in backend/.env) for fresher data.


## Implemented (2026-06-28) — Unified Admin Control Center + Trade Terms
**Admin auth unified under JWT** (ID `00001` / pwd `Shiv@12345`)
- [x] AdminLogin now uses ID + password → POST `/api/auth/admin/login`, JWT stored as `ln_admin_jwt`, sent as `Authorization: Bearer`. Legacy `X-Admin-Token` still accepted server-side; CSV export accepts JWT in `?token=`.
- [x] Unified `/admin-cms` dashboard: Dashboard, Content, Leads, Service Requests, Events, **Control Center**, Brain.
- [x] **Control Center** (new tab): live accent colour (CSS var `--ln-secondary`), maintenance mode + message, feature toggles (tools/services/brain/customs/intelligence/expo/academy/blog/trade_news), service-rate overrides, change-password. Saves via PUT `/api/admin/settings`.
- [x] **Live propagation**: `SettingsContext` fetches `/api/settings`; Nav hides toggled-off features; Layout renders maintenance screen for public site (admin stays accessible).
- [x] **Brain widget**: typing "I am admin" redirects to `/admin-login`.
- [x] **Customs Trade Terms** tab on `/customs-compliance`: Incoterms 2020, Payment Terms, Cargo Insurance, Key Trade Terms (from `/api/customs/trade-terms`).
- Verified end-to-end (test_reports/iteration_12.json — all 7 items PASS, site restored clean).


## Implemented (2026-06)
**Batch — Product Info Engine + cleanup + search fix** (Jun 2026)
- [x] **#1 Product Info Engine** (`/product-info`) rebuilt: free-text filters (Import/Export · Product · Origin · Destination · HSN optional), NO dropdowns, fully Brain-powered — works for ANY product worldwide (verified: saffron→USA, lithium battery→Germany). Clean markdown rendering (headings/bullets), sources + related + CTAs.
- [x] **#5** Home hero search fixed — was always navigating to /product-info; now routes the typed query to `/brain?q=` (Brain auto-answers). Different queries → different answers.
- [x] **#2** Removed Suppliers + Directory (fake data) — nav/footer links gone; `/suppliers` + `/directory` redirect to home.
- [x] **#3** Removed Network + Marketplace from nav/footer; pages now show an "in the app" note (`AppFeatureNote`) with download CTAs.
- [x] **#6** Home "Business Services" highlight section (Explore Services + IEC/GST/RCMC/Company tiles).
- [x] Nav "Platform" menu removed; Intelligence moved into Explore. Brain page + widget markdown rendering upgraded.
- Verified: testing_agent iteration_11 — 100% (6/6 areas), zero issues.
- DEFERRED to next batch: #4 (Incoterms/Insurance/Payment/CIF/FOB in Customs) and #7 (admin login 00001/Shiv@12345 via "I am admin" in Brain + Admin Control Center). Auth playbook (JWT) already obtained.


- [x] **Global back button** — top-left on every page except Home and Admin (`BackButton.jsx` in Layout; navigate(-1) with home fallback).
- [x] **Rebuilt `/customs-compliance`** as a product-based India hub with 8 tools (all buttons functional, loop closed):
  - **Compliance Report** — filters: product / direction (Export·Import) / country / HSN(optional) → `POST /api/customs/profile`: BCD+IGST+SWS, FTA detection, documents (product-specific), CHA clearance steps, government benefits, official ICEGATE/DGFT/Indian-Trade-Portal deep links + "Ask the Brain".
  - **Currency Exchange** — `GET /api/customs/fx` GENUINELY LIVE via open.er-api.com (no key, 1h cache).
  - **CBM Calculator**, **CHA Charges Estimator**, **Landed/Selling Price Calculator**, **Freight Routes**, **Government Benefits Finder**, **CHA Directory** (WhatsApp connect).
- [x] **Real-Time Trade Data Engine** (`customs.py`): live FX + curated India ruleset + Brain; **paid-API adapter** (`TradeDataProvider`, env `TRADE_DATA_PROVIDER`/`TRADE_DATA_API_KEY`) ready to flip on Seair/Export Genius/Volza with zero code change (Option C).
- Note: DGFT/ICEGATE have NO free public API and scraping isn't allowed — duty data is curated+Brain, clearly labelled "indicative" with official deep-links; upgradeable via the adapter.
- Verified: testing_agent iteration_10 — 100% (14/14 backend + all 8 tabs + back button), zero issues.


- Root cause: several cards looked clickable (cursor/arrow/play affordances) but had no destination. Core flows (nav, forms, detail pages, search, Brain) were actually working.
- Built automated full-site interaction audit via testing_agent (clicks every button/link/form, reports dead elements) — iterations 8 (audit) + 9 (verify).
- [x] **Academy**: new `/academy/:slug` lesson page (backend `GET /api/academy/{slug}` with generated curriculum + related courses); course cards now link; per-lesson "Ask the Brain to teach this" + "Learn with the Brain" → `/brain?q=` auto-ask.
- [x] **Trade News**: new `/trade-news/:id` detail page; featured + cards now link; "Ask the Brain about this story" + "More headlines".
- [x] **Marketplace**: listings → WhatsApp enquiry links; reels → `#download` with "Watch in app" badge.
- [x] **Suppliers**: per-card "Connect with supplier" WhatsApp action. **Network**: per-member "Connect" → /contact.
- [x] **Brain page** reads `?q=` and auto-submits.
- Verified: testing_agent iteration_9 — 100%, zero dead elements remaining, zero console/network errors, no regressions.


- [x] **Global Brain Widget** on every page (desktop floating bottom-right above WhatsApp; mobile FAB). Hidden on /admin and /brain. Mounted in Layout.
- [x] **Context-aware**: widget detects current route → page_context {type, slug}; backend `_resolve_page_entity` injects the country/product/HSN/service entity so short questions ("What documents are required?") work in-context.
- [x] **Page-specific suggested prompts** per page type (country/product/hsn/service/corridor/industry/marketplace/academy/default).
- [x] **Recommendation engine**: `recommendations` (related products/countries/HSN/services/blogs/academy/corridors/industries from KB) on every answer.
- [x] **Smart lead-gen CTAs**: `ctas` (Create Account, Download App, Book Consultation, Apply IEC, Contact) surfaced naturally by detected intent — no pop-ups.
- [x] **Personalization by role** (exporter/importer/cha/buyer/supplier) from user_context → boosts relevant engines.
- [x] **Multilingual-ready** (`language` param → en/hi/ar/fr/es prompt instruction) + **voice-ready** architecture (no STT implemented). Cache key includes page+lang+role.
- [x] Same Brain APIs reused by web/app/portals. Tested: testing_agent iteration_7 — 100% backend + frontend, zero issues.


- [x] **Live AI ON** via Emergent Universal LLM key. Default model `gpt-5.4-mini` (cheapest reliable). Env-configurable: `BRAIN_AI_PROVIDER` (openai/anthropic/gemini/local), `BRAIN_AI_MODEL`, `BRAIN_AI_ENABLED`. Zero app-code change to switch providers.
- [x] **RAG**: every answer retrieves Knowledge Base + engine context BEFORE generation; LLM reasons over LeadNation data only and states when info is insufficient (no fabrication). Source attribution preserved (enginesUsed + sources).
- [x] **Cost controls (CTO)**: 24h response caching (`brain_cache`) → repeat questions cost $0; deterministic engine-composition fallback if LLM fails/zero-budget → never breaks. Retry-once on transient errors.
- [x] **Brain Universal Search** replaces global search: KB → DB(CMS) → Engines/Network(suppliers,buyers,tools) → External APIs(off) → Web(off); relevance-ranked; new types: supplier, buyer, faq, learning, compliance, scheme. Frontend `/search` now calls `/api/brain/search`.
- [x] **Memory**: conversation_memory + user_context (preferred country/products/industries, role, recent searches, saved items) injected into RAG context.
- [x] **Monitoring**: `brain_usage` logs tokens + estimated cost + cached flag per call. Rate limiting (20 req/60s per session). Logging + retry.
- [x] **Admin `/admin/brain` expanded**: AI Health (live status, cache hit rate, degraded calls), Cost Monitoring (total + by model), Token Usage, Engine Health, KB stats (79 entries incl FAQs), Most Asked / Trending, Top + Most-Viewed Countries/Products, Most Used Services, Failed Queries, Knowledge Gaps, Reseed.
- [x] **Tested**: testing_agent iteration_6 — 100% (62/62 backend + all frontend), zero issues.
- Approx cost @ gpt-5.4-mini ≈ $0.0004–0.0005 per uncached query (caching drives effective cost far lower).


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

---

## VBIE P0 — Official Bulk-Data Foundation (implemented Aug 2026)
Full research report: `/app/memory/research/VBIE_BULK_SOURCES_RESEARCH.md` (legal matrices, country-by-country, 5-yr roadmap).

**Sources live (all legally GREEN, per-source legal-approval gated via `APPROVED_SOURCES`):**
- **GLEIF LEI (CC0)** — global identity backbone. `resolve_lei()` + `connector_gleif_enrich()` map buyers to a canonical LEI (self-healing re-link so a source re-upsert never wipes the identity evidence). All future registries/signals unify via GEID+LEI.
- **UK Companies House (OGL v3.0)** — hybrid: REST advanced-search API active (key in env `COMPANIES_HOUSE_API_KEY`, paginated within 600/5min); bulk-file path documented. Company-level only; no director/PSC personal data (GDPR).
- **Canada CID (OGL-Canada 2.0)** — bulk CSV importer signal (best-effort; empty from this host, guarded).
- **EU TED** — primary named-buyer signal (free reuse). **Trade.gov CSL** — mandatory sanctions screen.
- **SAM.gov** — kept DISABLED (`skipped_pending_legal`); D&B fields barred for prospecting.

**Freshness-merge / hard-delete engine** (`dedupe_and_prune`): records resolving to the same real company (LEI first, else country+normalized-name) are merged (evidence unioned into freshest) then stale duplicates HARD-DELETED. Admin-edited/deleted records never touched.

**Intelligence-not-raw-data presentation:** buyer API returns `intelligence` {trust_score, trust_band, confidence, freshness, source_reliability, lei} + `evidence_sources` (source LABELS). Locked payload shows intelligence + evidence labels but `provenance:[]` (cited detail gated). UI: `IntelligencePanel` in BuyerProfile.jsx (Trust/Confidence/Freshness/Source Reliability cards + LEI row + evidence chips).

**State:** ~11,722 real buyers (EU TED 10,590 + Companies House 1,000 + prior). ~80 LEI-matched. Tested: `/app/test_reports/iteration_37.json` — 8/8 backend + frontend, 11/11 acceptance criteria pass.

**Architecture invariants preserved:** website backend is the single writer of the buyer graph; one Mongo, one GEID, one Brain; web + app consume the same `/api/buyers/*`; no duplicate stores.

### VBIE backlog (P1+)
- **P1** Real-source expansion (all GREEN, official bulk-first): France SIRENE, Norway/Finland/Denmark/Czech, Singapore ACRA, Australia ABN, Japan NTA.
- **P1** Companies House official monthly BULK file loader (full ~5M snapshot) as base corpus; API for freshness.
- **P1** Scheduled GLEIF enrich across full corpus (throttled nightly batches) to grow LEI coverage.
- **P2** Yellow sources with guardrails: SEC EDGAR, Germany OffeneRegister, NL KVK, Poland, Brazil CNPJ.
- **REJECTED (do not ingest for commercial bulk):** Belgium CBE (€30k/yr), Italy Registro Imprese (paid), UN Comtrade redistribution (UN copyright), CIPC/Qatar; SAM.gov D&B fields.

---

## VBIE P1 — Recurring Continuous Intelligence Engine (implemented Aug 2026)
New module `backend/vbie_engine.py` turns VBIE from one-time ingestion into a permanent self-maintaining platform on the ONE shared MongoDB (one GEID, one Brain, single source of truth for web + app). Tested: `/app/test_reports/iteration_38.json` — 15/15 backend + frontend PASS.

**Multi-cadence scheduler** (config in Mongo `vbie_config._id='vbie_schedule'`, editable via admin):
- Weekly full refresh (Sun 02:00 UTC) → connectors → dedupe → brain recompute → change detection → alerts → weekly report.
- Daily incremental (03:00 UTC) → throttled GLEIF LEI enrich + rolling brain recompute + change detection + alerts (no full re-download).
- Monthly bulk (1st 04:00 UTC) → heavy bulk loaders (CH full register, SIRENE) when `bulk_enabled` (off by default; pod-safe cap).

**Duplicate Resolution Engine** (`dedupe_and_prune`, multi-key union-find): matches on LEI / company_number / registration_number / VAT / business_number / country+name; merges evidence+trust+provenance+identifiers into the freshest record; ARCHIVES obsolete dupes to `vbie_archive` (audit preserved) then HARD-DELETES. Admin-edited/deleted never touched.

**Freshness engine:** stored `freshness_score`/`freshness_label`, `last_source_sync`; stale records decay confidence/trust in brain.

**Brain automation** (`brain_recompute`, rolling batches): recomputes trust/confidence/freshness/source-reliability, re-screens sanctions (CSL), detects dissolved/inactive.

**Change detection + Buyer Change Alerts:** `detect_changes` → `vbie_changes` (status/address/name/legal/identity/trade); `fire_change_alerts` notifies subscribers watching a buyer (in-app `notifications` audience 'user' + Resend `buyer_changed` email). Watchlist: `buyer_watchlist` + `POST/DELETE /api/buyers/{geid}/watch`, `GET /api/buyers/watchlist` (auth). UI: "Watch for changes" button on buyer profile.

**Weekly Intelligence Report:** `build_weekly_report` → `vbie_reports` (new buyers, updated, duplicates merged/removed, dissolved, new countries/industries, failed connectors, LEI coverage, sync summary); admin endpoints list/generate/{id}/xlsx; emailed to admin (`weekly_report` template).

**Legal compliance matrix:** `validate_sources_legal` per-source (approved vs pending_legal_approval); auto-disables connectors flagged non-compliant. Admin: `GET /buyers/admin/legal`, `POST /buyers/admin/legal/{sid}`.

**Networking match:** `GET /api/buyers/match?name=&country=&number=` returns candidate buyer GEIDs to claim (links a joining verified company to its existing intelligence record).

**Bulk connectors:** `connector_companies_house_bulk` (monthly full-register ZIP, capped for pod, unbounded in prod) + `connector_sirene` scaffold (DORMANT until free INSEE_API_KEY + legal approval).

**Admin UI:** BuyersManager "Recurring Intelligence Engine" panel (schedule, recent cycles, approved-source chips, run daily/full cycle, download weekly report). NOTE: admin UI needs login (blocked in Emergent preview by DO CORS) — validated via X-Admin-Token backend endpoints.

**Email:** Resend wired (`RESEND_API_KEY`/`SENDER_EMAIL` in env). Actual inbox delivery requires the `leadnation.app` domain verified in Resend (owner DNS step); code path validated.

### VBIE P1 remaining / next
- **P1** Provide free INSEE_API_KEY → activate France SIRENE; add Norway/Finland/Denmark/Czech, Singapore ACRA, Australia ABN, Japan NTA connectors.
- **P1** Enable Companies House monthly BULK (`bulk_enabled=true`) in production to grow to full ~5M base corpus.
- **P1** Verify `leadnation.app` in Resend so subscriber change-alert + weekly digest emails actually deliver.
- **P2** Cross-backend GEID/entities single-writer enforcement (DO backend); subscriber-facing weekly digest email.
