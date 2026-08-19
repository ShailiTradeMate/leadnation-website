# Consolidated prompt for the Emergent app team (DO identity backend)
Paste everything below into the mobile-app Emergent project.

---

Hi team — I've built a complete, working reference of the **Verified Buyer completion + verification flow** on the LeadNation website using your live shared APIs. It works end-to-end today. I need you to mirror it into the DO backend so the mobile app and website share ONE verification system. Please read the architecture notes first, then the build request.

## PART A — Shared architecture (please confirm you follow this)
We verified the wiring and it is exactly as intended:
- **One Firebase project** (`trademate-new`) → each user has ONE `uid` across app + website.
- **One shared MongoDB Atlas database** (`leadnation` on `cluster0.tpcdrfx.mongodb.net`). BOTH the DO identity backend and the website backend connect to this same database. No syncing — it's one copy of the data.
- **Identity is owned ONLY by the DO backend**: `users`, `_counters` (5-digit Customer ID allocator), `company_profiles`, `members_bridge`, profile writes, GEID minting. The website is a pure client of these.
- **Join keys**: `uid` (machine key) + `customer_id` (5-digit human ID, e.g. 00002).
- **One admin for both**: `admin@leadnation.app` / Customer ID `00001`, `users.role == "admin"`. Admin actions on shared data apply to app + website because it's one database. IMPORTANT: for the app to *show* verification review/decisions, the app must READ the shared verification collections (see Part B), otherwise the data exists but isn't visible in the app.

Rule: keep identity/profile/Customer-ID/GEID single-writer on DO. The website will only call your APIs for those.

## PART B — Verification: what already works + what to build
### Already live on DO (confirmed working, thank you)
- `GET/PUT /api/v1/profiles/{uid}` (auth: Firebase Bearer + `x-user-uid`; PUT requires x-user-uid == path uid)
- `GET /api/v1/documents` (personal/business/trade catalog, country-specific)
- **GEID linking works**: `POST /api/entities` (member_company/prospect) + `POST /api/members/bind {uid,customer_id,geid}` → returned a real GEID `LN-prospect-01M0BHNNNRZ...`

### The reference pipeline I built (mirror these contracts on DO)
Website endpoints under `/api/verify` — please implement the same server-side, backed by the shared `leadnation` DB so the app can read them too:
1. `POST /upload` — store selfie + business document in **object storage (NOT base64 in Mongo)**; return `{id, url, kind}`. (You noted your OCR currently stores base64 — please add an object-storage upload endpoint, e.g. Emergent Object Storage or Spaces.)
2. `POST /analyze-selfie` — vision check returning JSON: `{is_human_face, face_count, ai_generated_likelihood (0..1), recapture_likelihood, quality_score, liveness_ok, confidence_real_person, reasons[]}` PLUS a **duplicate-face** check against previously verified faces.  → not built on your side yet.
3. `POST /analyze-document` — OCR + legitimacy: `{is_business_document, document_type, company_name, registration_number, address, country, legible, tamper_signs, confidence, extracted_text_summary}`. Your Google Vision OCR can back this; add a **government cross-check** where lawful.
4. `POST /submit` — RE-RUN the checks server-side (never trust the client), compute overall confidence, then decide:
   - **verified** (auto) when confidence ≥ 0.75 with a good selfie + valid business doc,
   - **needs_review** (human queue) when borderline or automation unavailable,
   - **rejected** when duplicate face / no human face / AI-fake.
   On verified/approved → call `POST /entities` + `POST /members/bind` and set `verification_status`.
5. `GET /admin/queue` + `POST /admin/{id}/decide` — human review approve/reject (the one shared admin uses this on both app + website).

Suggested collections in the shared DB (so app + website both read them): `verification_submissions`, `verification_face_index`. Store the checks, confidence, decision, reviewer, and the resulting GEID on each submission.

Decision thresholds I used (tune freely): auto-approve ≥ 0.75, AI-fake ≤ 0.35, quality ≥ 0.40, doc confidence ≥ 0.40, duplicate-face Hamming distance ≤ 8.

Required profile fields I gate completion on (aligned to your profile shape): `name, mobile, email, country, city, products, company_details.company_name`. (I dropped `company_details.address` because your profile schema didn't persist it — add it if you want address captured.)

## PART C — Three fixes/questions
1. **Intermittent `502 Bad Gateway` on `PUT /api/v1/profiles/{uid}`** — during testing it 502'd several times in a row, then recovered. Please check upstream stability/timeouts. (I added retries on my side as a stopgap.)
2. **Entity typing**: I requested `member_company` for an importer but `/entities` returned a `prospect` GEID. Please confirm your rules so buyers (importers) are typed as buyers.
3. **Cosmetic (non-urgent)**: rename `runtime.txt` → `.python-version` containing just `3.11` to clear the DO deprecation warning and auto-receive Python patches.

Once you expose the Part B endpoints (same JSON shapes), I'll repoint the website's verification calls from my reference backend to your DO endpoints — zero UI changes needed. Please share endpoint URLs, auth, and request/response payloads when ready. Thanks!
