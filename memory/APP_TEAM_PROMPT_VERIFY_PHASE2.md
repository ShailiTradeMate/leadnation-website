# Follow-up prompt for the Emergent app team (DO identity backend)

Copy-paste the section below to the mobile-app Emergent project.

---

Hi team — quick update + a request.

I've now built a **complete working reference of the Verified Buyer completion + verification flow on the LeadNation website**, using your live shared APIs. It works end-to-end today. Please mirror this logic into the DO backend so the mobile app and website share ONE verification system (website stays a client — DO stays the owner of identity/profile/GEID).

## What already works with your live APIs (thank you)
- `GET/PUT /api/v1/profiles/{uid}` (Firebase Bearer + `x-user-uid`; PUT requires x-user-uid == path uid)
- `GET /api/v1/documents` (personal/business/trade catalog)
- **GEID linking is live and works** — `POST /api/entities` + `POST /api/members/bind {uid,customer_id,geid}` returned a real GEID (e.g. `LN-prospect-01M0BHNNNRZ...`). 🎉

## The reference pipeline I built (please mirror on DO)
Website endpoints (prefix `/api/verify`) — copy the same contracts server-side:
1. `POST /upload` — stores selfie + business document in **object storage (NOT base64)**, returns a stored file id/url. → **You need to add an object-storage upload endpoint on DO (you noted your OCR currently stores base64).**
2. `POST /analyze-selfie` — vision check returning JSON: `is_human_face`, `face_count`, `ai_generated_likelihood (0..1)`, `recapture_likelihood`, `quality_score`, `liveness_ok`, `confidence_real_person`, `reasons[]`, plus a **duplicate-face** check against previously verified faces. → **Not built on your side yet.**
3. `POST /analyze-document` — OCR + legitimacy: `is_business_document`, `document_type`, `company_name`, `registration_number`, `address`, `country`, `legible`, `tamper_signs`, `confidence`. (Your Google Vision OCR can back this; add a **government cross-check** where lawful.)
4. `POST /submit` — re-runs checks server-side (never trusts the client), computes an overall confidence, then decides:
   - **verified** (auto) when confidence ≥ 0.75 and a valid business doc + good selfie,
   - **needs_review** (human queue) when borderline or automation unavailable,
   - **rejected** when duplicate face / no human face / AI-fake.
   On **verified/approved** it calls your `POST /entities` + `POST /members/bind` and sets `verification_status`.
5. `GET /admin/queue` + `POST /admin/{id}/decide` — human review → approve/reject.

Decision thresholds I used (tune as you like): auto-approve ≥ 0.75, AI-fake ≤ 0.35, quality ≥ 0.40, doc confidence ≥ 0.40, duplicate-face Hamming distance ≤ 8.

## Two things I need from you
1. **Build the missing DO endpoints above** (object-storage upload, selfie/liveness/AI-fake/duplicate-face, document OCR + gov cross-check, and the submit → review → decision workflow) using the exact JSON shapes above so the website can point at them with zero UI changes. Please share the endpoint URLs, auth, and request/response payloads when ready.
2. **Please investigate an intermittent `502 Bad Gateway` on `PUT /api/v1/profiles/{uid}`** — during testing it 502'd several times in a row, then recovered. It occasionally blocks profile updates. A quick look at upstream stability/timeouts would help.

Also minor: for an **importer** I requested entity type `member_company` but `/entities` returned a `prospect` GEID — please confirm your entity-typing rules so buyers are typed correctly.

Once you expose these, I'll repoint the website's verification calls from my reference backend to your DO endpoints. Thanks!
