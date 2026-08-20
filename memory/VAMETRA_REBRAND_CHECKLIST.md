# Vametra AI Rebrand — Master Migration Checklist
**Date:** 2026-08-19 · **From:** LeadNation → **To:** Vametra AI
**Public brand:** Vametra AI · **Legal entity:** Vametra AI Technologies Pvt. Ltd. · **Primary domain:** https://vametra.com (non-www canonical)

> RULE APPLIED: Only CUSTOMER-FACING branding was changed. All INTERNAL technical identifiers stay "LeadNation" until a deliberate technical migration (shared MongoDB `DB_NAME`, DO identity backend hostname, Firebase project `trademate-new`, `LN-` GEID prefix, admin login identity, internal code/collection names, connector User-Agent).

---
## ✅ DONE IN CODE (this session — ships on next deploy)
### Website — Frontend
- [x] Brand word "LeadNation" → "Vametra AI" across all `frontend/src` pages & components (54 files)
- [x] Central brand config `src/lib/brand.js`: `BRAND_NAME`, `SITE_URL` → https://vametra.com, one-liner
- [x] New logo mark generated & wired (`/brand/vametra-mark.png`) in Nav + Footer
- [x] Nav item, hero copy, cookie banner, report footers → Vametra AI / vametra.com
- [x] Email/social handles intentionally KEPT (`admin@leadnation.app`, IG `leadnation.app`, LinkedIn `leadnation-app`) until Vametra equivalents are ready

### Website — SEO / GEO / PWA
- [x] `public/index.html`: `<title>`, meta description/keywords, canonical → vametra.com, OG + Twitter tags, all 3 JSON-LD blocks (Organization/SoftwareApplication/WebSite), `@id`, logo/image URLs
- [x] `public/manifest.json`: short_name + name → Vametra AI
- [x] `public/sitemap.xml`: all 77 URLs → https://vametra.com
- [x] `public/robots.txt`: Sitemap URLs → vametra.com; AI-crawler citation note → Vametra AI
- [x] `public/llms.txt`: brand + URLs → Vametra AI / vametra.com (contact email + socials kept)
- [x] Favicon + app-icon set regenerated from new Vametra icon: `favicon.ico`, `favicon-16.png`, `favicon-32.png`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`
- [x] `og-default.png` social share card regenerated with Vametra AI branding
- [x] Backend `seo.py`: SITE constant + IndexNow host → vametra.com
- [x] `SEO.jsx` uses SITE from brand.js (auto-updated)

### Backend
- [x] Brand strings → Vametra AI in: Brain (`brain/*`), engines, news_engine, costing_engine, decision_engine, adapters, vbie*, monetize (invoices + referral link), services (FAQs), content (blog), pricing labels, ai.py, reference.py root message, server.py API title
- [x] `emailer.py`: BRAND, COMPANY, HTML header logo (was split-tag `Lead<span>Nation`), footer, all templates → Vametra AI
- [x] `backend/.env`: `PUBLIC_SITE_URL` → https://vametra.com · `SENDER_EMAIL` display name → "Vametra AI" (address kept `noreply@leadnation.app` until Resend verifies vametra.com) · `CORS_ORIGINS` → added vametra.com + www.vametra.com (kept leadnation.app for redirect window)
- [x] Brain response cache (`brain_cache`) cleared so answers regenerate with new branding
- [x] Verified: backend healthy, returns "Vametra AI API"; homepage + Contact/Pricing/Legal render with new brand

---
## ⏳ USER / OPS ACTIONS (outside code — do before/at go-live)
### Domain & DNS
- [ ] Point **vametra.com** (A/CNAME) to the app host; issue SSL cert
- [ ] 301 redirect **www.vametra.com → vametra.com**
- [ ] 301 redirect **leadnation.app → vametra.com** (and www.leadnation.app)
- [ ] Update deploy platform env vars to mirror the new `.env` (PUBLIC_SITE_URL, CORS_ORIGINS, SENDER_EMAIL) then **redeploy**

### Firebase (identity stays `trademate-new` — DO NOT rename)
- [x] `vametra.com` added to **Firebase → Auth → Authorized domains** (owner, screenshot confirmed)
- [x] **Super-admin email migrated** (2026-08-20): admin@leadnation.app → **admin@vametra.com** via Firebase Admin SDK — same UID `gq5pHUPD3LPXNhycRHSdhmkhPiS2`, same password, customer_id 00001 + role admin unchanged; Mongo `users` doc synced by uid. Verified: REST login + backend token auth + `GET /api/admin/collections` → 200.
- [ ] (Optional) Add current preview host to Authorized domains only if testing Google OAuth in preview (email/password login unaffected)

### Email (Resend)
- [x] Contact email updated to **admin@vametra.com** (Contact page, Footer, Legal, index.html contactPoint, llms.txt, SEO JSON-LD)
- [x] Social handles updated: Instagram **@vametra_ai**, LinkedIn **vametra** (brand.js + index.html sameAs + llms.txt)
- [x] `ADMIN_EMAIL` (admin alert recipient) → admin@vametra.com
- [x] vametra.com domain **Verified** in Resend (DNS/SPF/DKIM done by owner)
- [x] **Resend API key swapped** (2026-08-20) → key authorized for vametra.com; `SENDER_EMAIL` now `Vametra AI <noreply@vametra.com>`. Real test send from vametra.com → **success**. Owner also updated the key on the DO backend.
- [ ] If the **DO identity backend** sends any email (welcome/OTP), confirm ITS sender is `@vametra.com` too (owner updated the key already).
- [ ] Set up receiving mailboxes: hello@, support@, admin@, noreply@ vametra.com (admin alerts now route to admin@vametra.com)

### SEO / Analytics tooling
- [ ] **Google Search Console**: add vametra.com property, verify, submit sitemap, use Change-of-Address tool from leadnation.app (if verified there)
- [ ] **Bing Webmaster Tools**: add vametra.com, submit sitemap
- [ ] **IndexNow**: host the `{INDEXNOW_KEY}.txt` file at vametra.com root (key already used by backend `seo.py`)
- [ ] **GA4 / GTM / Clarity**: add vametra.com as a data stream / allowed domain (env IDs unchanged: GA4 G-H5809GHQXW, GTM-5JM23MH4, Clarity y2xx93q69j)
- [ ] **PostHog**: add vametra.com to allowed origins (key in index.html)
- [ ] **Meta Pixel**: set `REACT_APP_META_PIXEL_ID` when ready

### Payments
- [ ] **Stripe**: update account/business branding, statement descriptor, and (if using) Checkout branding + webhook endpoint URL → vametra.com/api/webhook/stripe
- [ ] **Razorpay**: update business name/branding in dashboard, checkout logo, and webhook URL → vametra.com; keys unchanged (`RAZORPAY_*` in .env)

### App (DO app team — coordinate)
- [ ] Rename app display name → Vametra AI; regenerate mobile brand assets (old ones remain in `frontend/public/brand/`: `app_icon.png`, `splash_screen.png`, `logo_horizontal_*.png`, `logo_mark.png`, `ln-icon.png` — NOT used by website, used by app)
- [ ] **App Store** listing: name, subtitle, screenshots, description, privacy URLs → vametra.com
- [ ] **Play Store** listing: title, short/full description, graphics, privacy URLs → vametra.com
- [ ] Deep-link domains: swap to vametra.com when web routes exist
- [ ] Backend/DB/Firebase/Customer-IDs/GEID stay LeadNation internally (per frozen architecture) — no change

### Social
- [ ] Create Vametra Instagram + LinkedIn (+ optional X/YouTube)
- [ ] Update `brand.js` SOCIALS + index.html `sameAs` + llms.txt to new handles; redirect old profiles

### Documentation & Legal
- [x] Legal pages (`/legal/*`) brand text → Vametra AI (email kept until migrated)
- [ ] Update legal entity references, contact email on legal pages after email migration
- [ ] Update any external docs, decks, PDFs, email signatures, invoices letterhead

---
## 🔒 INTENTIONALLY UNCHANGED (internal — verify these still say leadnation)
- `backend/.env` → `DB_NAME="leadnation"`, `MONGO_URL`, `ADMIN_EMAIL="admin@leadnation.app"`, `AUTH_API_BASE` (DO host), `ADMIN_TOKEN`
- `frontend/.env` → `REACT_APP_AUTH_API_BASE` (DO host), `REACT_APP_FIREBASE_*` (`trademate-new`)
- GEID prefix `LN-` on existing entities · `vbie_connectors.py` User-Agent · collection names · internal code identifiers · admin Firebase login identity
