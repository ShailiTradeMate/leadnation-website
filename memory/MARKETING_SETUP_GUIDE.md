# Vametra AI — Marketing, Analytics, SEO & GEO Setup Guide
Owner action guide. Created June 2026. Collect the values in the "Give me" boxes and paste them in chat — I will wire them into the app.

---

## 0. What is ALREADY live in the code (no action needed)
| Item | Status | Where |
|---|---|---|
| GA4 measurement ID | `G-H5809GHQXW` configured | `frontend/.env` → `REACT_APP_GA4_ID` |
| Google Tag Manager container | `GTM-5JM23MH4` configured | `REACT_APP_GTM_ID` |
| Microsoft Clarity project | `y2xx93q69j` configured | `REACT_APP_CLARITY_ID` |
| Meta Pixel | **empty — needs ID** | `REACT_APP_META_PIXEL_ID` |
| Cookie consent gate (GDPR opt-in) | Live — tags only fire after "Accept" | `src/lib/analytics.js`, `CookieConsent.jsx` |
| Event tracking (signup, login, brain query, PDF, payments…) | Live, PII-scrubbed | `EVENTS` in `analytics.js` |
| robots.txt with AI/GEO bots allowed (GPTBot, PerplexityBot, ClaudeBot…) | Live | `public/robots.txt` |
| sitemap.xml (77 URLs) + dynamic `/api/sitemap.xml` | Live | `public/sitemap.xml` |
| JSON-LD: Organization, FAQ, Breadcrumbs, per-page SEO | Live | `src/components/SEO.jsx` |
| OG / Twitter cards + new logo share image | Live | `public/index.html`, `og-default.png` |

**Important:** verification meta tags are not in the code yet, and the live site must be deployed on `vametra.com` before search consoles can verify.

---

## 1. Google Tag Manager (control tower — do this first)
1. Go to https://tagmanager.google.com → your container `GTM-5JM23MH4` (create a new **Web** container if you lost access).
2. Admin → Install Google Tag Manager → note the container ID.
3. Inside GTM create these **Variables** (Data Layer Variable) so our events carry context:
   `location`, `plan`, `tool`, `country`, `hs_code`, `amount`, `currency`.
4. Create **Triggers** of type *Custom Event* for each of our event names:
   `user_registered`, `user_login`, `brain_query`, `command_center_opened`,
   `trade_project_created`, `quote_generated`, `pdf_report_created`, `pdf_report_downloaded`,
   `subscription_started`, `payment_attempt`, `payment_success`, `payment_failure`,
   `download_app_click`.
5. Create **Tags**: GA4 Event tags mapped to the triggers above (one tag can serve many with a `{{Event}}` name).
6. Use **Preview / Tag Assistant** on the live site → confirm events fire → **Submit** the version.

> Give me: GTM container ID (if it changed) + confirmation that the container is published.

---

## 2. Google Analytics 4
1. https://analytics.google.com → Admin → Data Streams → Web stream for `vametra.com`.
2. Copy the **Measurement ID** (`G-…`) — verify it matches `G-H5809GHQXW`; if not, send me the new one.
3. Admin → Data Streams → Enhanced measurement: ON (scrolls, outbound clicks, site search, file downloads).
4. Admin → Events → **Mark as conversion**: `user_registered`, `subscription_started`, `payment_success`, `download_app_click`, `pdf_report_created`.
5. Admin → Data Settings → Data Retention → **14 months**.
6. Admin → Product Links → link **Google Search Console** and **Google Ads** (after step 4/8).
7. Admin → Reporting identity → Blended. Enable **Google signals** if you want demographics.
8. Create Audiences: "Signed up", "Used a tool", "Viewed pricing, no signup" (for remarketing later).

> Give me: GA4 Measurement ID (confirm/new) + the Google account email you want as property admin.

---

## 3. Microsoft Clarity (heatmaps + session recordings)
1. https://clarity.microsoft.com → project for `vametra.com` → Settings → Overview → copy the **Project ID** (confirm `y2xx93q69j`).
2. Settings → Integrations: connect **GA4** (recordings link into GA4 segments).
3. Settings → Masking: set to **Balanced** or **Strict** — critical, because buyer/company data must never be recorded.
4. Create Smart Events / funnels: signup → verify → tool used → pricing view.
5. After 48h of traffic, review Dead clicks, Rage clicks, Scroll depth — especially **mobile**.

> Give me: Clarity Project ID (confirm/new).

---

## 4. Google Search Console
1. https://search.google.com/search-console → Add property → choose **Domain** property `vametra.com` (preferred, covers www + http/https).
2. Verification: it will give you a **TXT record** → add it in GoDaddy DNS (Type TXT, Host `@`, Value `google-site-verification=…`).
   - Alternative if DNS is awkward: choose *URL prefix* property → **HTML tag** method → send me the `content="…"` token and I will put the meta tag in `index.html`.
3. Once verified: Sitemaps → submit `https://vametra.com/sitemap.xml` and `https://vametra.com/api/sitemap.xml`.
4. Settings → Users → add your team as Full users.
5. URL Inspection → request indexing for: `/`, `/tools`, `/tools/duty-calculator`, `/tools/hsn-finder`, `/buyers`, `/pricing`, `/brain`, `/expo`, `/trade-news`.
6. Enable email alerts; check **Core Web Vitals** and **Mobile Usability** reports weekly for the first month.

> Give me: the GSC HTML-tag verification token (or tell me the DNS TXT is done).

---

## 5. Bing Webmaster Tools + Bing/Microsoft Search Console
1. https://www.bing.com/webmasters → Add site `https://vametra.com`.
2. Fastest path: **Import from Google Search Console** (one click, brings verification + sitemaps).
3. Manual path: verification via **Meta tag** (`msvalidate.01`) → send me the token, or the BingSiteAuth.xml file / DNS CNAME.
4. Submit sitemaps (same two URLs as above).
5. Enable **IndexNow** — Bing gives you an API key file (`<key>.txt`) to host at the site root. Send me the key and I will add the file + ping IndexNow automatically whenever news/expo/blog content changes (this also feeds Copilot).
6. Turn on **Bing Places / Microsoft Clarity link** inside Webmaster Tools.

> Give me: Bing verification token (`msvalidate.01`) + IndexNow API key.

---

## 6. SEO — on-page and technical (what I will do once keys arrive)
Already done: canonical tags, per-page titles/descriptions, Organization/FAQ/Breadcrumb JSON-LD, robots, sitemaps, OG images, mobile-first layout, fast font loading.

Next, in priority order:
1. **P0 — Programmatic SEO pages.** We already have country/product/corridor/HS routes. Give each a unique H1, 300+ words of real data, FAQ block and internal links: e.g. *"Export basmati rice from India to UAE — duty, HS code, documents"*. This is the single biggest traffic lever (thousands of long-tail pages).
2. **P0 — Tool landing pages** with schema `SoftwareApplication` + `HowTo`: duty calculator, HS finder, landed cost, export incentives, find buyers.
3. **P1 — Blog cluster plan** (pillar + spokes): Customs & compliance, HS codes, Incoterms & landed cost, FTAs, Export finance, Country guides. 2 posts/week, each 1,200+ words with a data table and internal links to a tool.
4. **P1 — Article/NewsArticle schema** on blog + trade news, `Event` schema on expo pages (gets you into Google Events), `Product`/`Dataset` schema on product pages.
5. **P1 — Image SEO**: descriptive alt text + filenames, WebP, lazy loading.
6. **P2 — hreflang** if/when you add regional variants; `Speakable` schema for voice.
7. **P2 — Core Web Vitals pass**: code-split the globe/3D, preload the hero font, compress the new logo PNGs to WebP.
8. **Monthly**: broken-link + 404 sweep, orphan-page check, duplicate-title check.

> Give me: your top 20 target keywords (or let me research and propose them), and the 5 countries/corridors you most want to rank for.

---

## 7. GEO — Generative Engine Optimisation (ChatGPT, Gemini, Perplexity, Copilot)
This is where trade buyers will increasingly search. Already done: AI crawlers explicitly allowed in robots.txt, FAQ schema everywhere.

To do:
1. **llms.txt** at the site root — a plain-text map of what Vametra AI is, key URLs and data definitions, which LLM crawlers read preferentially. I can generate it.
2. **Answer-first content format**: every page opens with a 40-60 word direct answer, then detail — this is what gets quoted.
3. **Citable data blocks**: "India → UAE basmati duty: X%" as clean tables with dates and sources. AI engines cite structured, dated facts.
4. **Entity consistency**: identical name, legal name, address, founder, logo and socials on site, LinkedIn, Instagram, Crunchbase, Google Business Profile and Wikidata. Strengthens the knowledge graph.
5. **Third-party presence** (AI engines heavily cite these): Reddit r/ImportExport, Quora, LinkedIn articles, Medium, G2/Capterra/Product Hunt listings, IndiaMART/Trade blogs, Wikipedia-adjacent references.
6. **Track AI referrals**: I will add GA4 channel grouping for `chatgpt.com`, `perplexity.ai`, `gemini.google.com`, `copilot.microsoft.com` so you can see AI-driven traffic.
7. **Monthly prompt audit**: ask ChatGPT/Perplexity "best export duty calculator for India", "how to find verified buyers in UAE" → record whether Vametra AI is cited; fix the gaps.

> Give me: nothing needed — but tell me if you want a Product Hunt / G2 launch, and I will prep the assets.

---

## 8. Recommended extras for reach (my additions)
| Channel | Why | What I need from you |
|---|---|---|
| **Google Business Profile** | Local + brand knowledge panel, reviews | Business verification (postcard/phone) done by you |
| **Google Ads** (Search, brand + high-intent) | "customs duty calculator", "HS code India" convert fast | Ads customer ID + conversion linker permission |
| **Meta Pixel + Conversions API** | Retargeting exporters on IG/FB; pixel slot is empty | Meta Pixel ID (+ CAPI token if you want server-side) |
| **LinkedIn Insight Tag** | B2B trade audience is on LinkedIn; enables matched audiences | LinkedIn Partner ID |
| **X (Twitter) Pixel / Reddit Pixel** | Cheap B2B reach, trade communities | Pixel IDs |
| **Email marketing** (Resend is already wired) | Weekly "Trade Brief" newsletter from your live news engine → the cheapest retention channel | Approve: I build newsletter signup + weekly digest cron |
| **WhatsApp Business broadcast** | Your audience is WhatsApp-first (button already on site) | WhatsApp Business API / Twilio decision |
| **Referral / invite program** | Verified-buyer marketplace grows via referrals | Approve reward rules |
| **App store optimisation** | If the Android/iOS app lists, ASO keywords + screenshots with the new logo | Store console access |
| **Uptime + speed monitoring** | SEO is punished by downtime | Approve: add health-check monitor |
| **Schema for reviews/testimonials** | Star ratings in SERPs raise CTR | 5-10 real customer quotes |

---

## 9. Paste-back checklist (what to send me next chat)
```
GTM container ID:               GTM-____________  (published? yes/no)
GA4 Measurement ID:             G-______________
Clarity Project ID:             ________________
Google Search Console token:    google-site-verification=____________  (or "DNS TXT done")
Bing verification token:        msvalidate.01=____________
Bing IndexNow API key:          ________________
Meta Pixel ID:                  ________________  (optional)
LinkedIn Partner ID:            ________________  (optional)
Google Ads Customer ID:         ___-___-____      (optional)
Target keywords (top 20):       ________________
Priority countries/corridors:   ________________
```

## 10. Order of operations
1. Deploy to `vametra.com` (consoles cannot verify a preview URL).
2. GTM → GA4 → Clarity (measurement first, so you have a baseline).
3. Search Console + Bing + IndexNow (indexing).
4. Sitemap submit + request indexing of the 9 money pages.
5. SEO content engine (programmatic pages, then blog cadence).
6. GEO (llms.txt, answer-first rewrites, third-party presence).
7. Paid + email + WhatsApp retargeting once organic baseline exists.
