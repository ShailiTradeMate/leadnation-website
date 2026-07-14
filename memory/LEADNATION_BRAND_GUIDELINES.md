# LEADNATION — BRAND GUIDELINES

_Brand: **LeadNation** · Company: **Vametra AI Technologies Pvt Ltd** · v1.0 · 2026-07-07_
_Category: AI-powered Global Trade Intelligence Platform · Feel: Bloomberg × OpenAI × Global Trade Network_

> STATUS: **CONCEPTS FOR APPROVAL.** The live website logo has **NOT** been replaced.
> Preview assets live in `/app/frontend/public/brand/` → viewable at `https://leadnation.app/brand/<file>`
> (after next redeploy) or in preview now.

---

## 1. LOGO

**Concept:** A geometric **"LN" monogram** fused with a **globe of connected network nodes** and a subtle
**upward trade-route arc/arrow** — expressing AI + global connectivity + trade growth. Simple enough to read
at favicon size, premium enough for a Bloomberg-grade product.

| Asset | File (`/brand/`) | Use |
|---|---|---|
| Primary logo — dark | `logo_horizontal_dark.png` | Dark backgrounds (site nav, footer) |
| Primary logo — light | `logo_horizontal_light.png` | White/light backgrounds, documents |
| Icon / mark only | `logo_mark.png` | Standalone symbol, watermarks, small spaces |
| App icon | `app_icon.png` | Mobile app icon (rounded-square, gradient) |
| Splash screen | `splash_screen.png` | Mobile app launch screen concept |

**To finalize (designer, after you pick a direction):** redraw the chosen concept as **SVG (vector)**,
then export PNGs at all sizes + a **transparent-background** master + **favicon.ico**. (Image-generated PNGs
are concept references; the production logo should be true vector so it scales crisply and edits cleanly.)

### Logo usage rules
- **Clear space:** keep padding ≥ the height of the "N" around the logo on all sides.
- **Minimum size:** wordmark ≥ 120px wide on screen; mark ≥ 24px.
- **Backgrounds:** dark navy (preferred) or white only. Avoid busy photos behind the wordmark — use the mark on a solid chip instead.
- **Do NOT:** stretch/skew, recolor outside the palette, add drop shadows/outlines, rotate, or place the cyan-on-navy version on a light background (use the light version).
- Always spell it **"LeadNation"** — one word, camel-case, capital L and N. Never "Lead Nation" or "Leadnation".

---

## 2. COLOR PALETTE

| Role | Name | HEX | Notes |
|---|---|---|---|
| Background (base) | Deep Space Navy | `#05070f` | App/site canvas |
| Surface / panel | Panel Navy | `#0b1120` | Cards, headers |
| Border / line | Slate Line | `#1c2740` | Dividers, borders |
| **Primary accent** | **Signal Cyan** | `#00C2FF` | CTAs, links, brand highlight |
| Secondary accent | Electric Blue | `#2563EB` | Gradient partner to cyan |
| Success / live | Emerald | `#10B981` | "Live" news, approved states |
| Attention | Amber | `#F59E0B` | Featured, warnings |
| Text primary | White | `#FFFFFF` | Headings |
| Text body | Slate 200 | `#C3CCDD` | Paragraphs |
| Text muted | Slate 500 | `#5B6B86` | Captions, footers |

**Signature gradient:** `#00C2FF → #2563EB` (135°). Use sparingly for the mark, key CTAs, and hero accents.

---

## 3. TYPOGRAPHY

- **Display / Headings:** `Sora` or `Space Grotesk` (geometric, modern, confident). Weights 600–800.
- **Body / UI:** `Inter` (clean, neutral, excellent legibility). Weights 400–600.
- **Mono / data:** `JetBrains Mono` or `IBM Plex Mono` for figures, HSN codes, labels (uppercase, letter-spaced).
- **Email wordmark:** serif `Georgia` fallback is acceptable in email clients (already in use).
- Type scale: H1 `text-4xl→6xl`, H2 `text-lg`, body `text-base`, labels `text-xs` uppercase tracking-widest.

---

## 4. TAGLINE

> **OFFICIAL TAGLINE (locked 2026-07-14): "Intelligence Beyond Borders"** — use this exact wording everywhere (site, SEO, OG, email, structured data, app). The list below is the original brainstorming archive only.

**20 candidates** (original — screened against major brands; none match known slogans. "The Trade Desk"
is a listed adtech company, so we avoid that exact phrase):

1. Intelligence for Global Trade
2. The AI Brain for Global Trade
3. Global Trade, Decoded
4. Borderless Trade, Brilliant Decisions
5. Trade Intelligence Beyond Borders
6. Where Global Trade Thinks
7. Your Command Center for World Trade
8. Smarter Trade, Everywhere
9. The Intelligence Layer for World Trade
10. Decisions That Cross Borders
11. Trade Beyond Borders — Powered by AI
12. From Data to Trade Decisions
13. Every Border, One Intelligence
14. Trade the World with Confidence
15. The Operating System for Global Trade
16. Turn Trade Data into Decisions
17. Intelligence That Moves Goods
18. Your Global Trade Co-Pilot
19. Command the World's Trade
20. Borderless Trade, Brilliant Intelligence

**⭐ Recommended top 3:**
- **1st — "Intelligence for Global Trade"** — clear, ownable, keyword-rich for SEO, premium.
- **2nd — "The AI Brain for Global Trade"** — anchors to your flagship *LeadNation Brain* product.
- **3rd — "Global Trade, Decoded"** — short, memorable, confident.

_Before trademark registration, run a formal search (India IP Office, USPTO, EUIPO). These are descriptive
straplines, low conflict risk, but verify for your class (Nice Class 9/35/42)._

---

## 5. SOCIAL & CHANNEL ASSETS

| Asset | Spec | Direction |
|---|---|---|
| Profile image | 400×400 (round) | `logo_mark` centered on Deep Space Navy chip |
| Social share (OG) | 1200×630 | `og-default.png` (already live) |
| LinkedIn cover | 1584×396 | Globe + trade arcs, wordmark left, tagline |
| X/Twitter header | 1500×500 | Same system, wider crop |
| YouTube banner | 2560×1440 (safe 1546×423) | Wordmark centered in safe area |
| Email header | text wordmark (no image) | "LeadNation by Vametra AI Technologies Pvt Ltd" (already live) |
| PDF report header | wordmark + thin cyan rule | Reuse light logo on white |

**Profile copy (prepared — do NOT create accounts):**
- **Instagram bio:** `LeadNation — Intelligence for Global Trade 🌐 AI trade decisions, costing, compliance & buyer intel. Built by Vametra AI. 👇 leadnation.app`
- **LinkedIn (company):** `LeadNation is an AI-powered global trade intelligence platform by Vametra AI Technologies Pvt Ltd — helping exporters, importers, manufacturers and trade professionals make faster, smarter cross-border decisions with the LeadNation Brain, Trade Command Center, costing & compliance engines, and real-time trade news. Intelligence for global trade. leadnation.app`
- **X/Twitter bio:** `AI-powered global trade intelligence. Brain • Command Center • costing • compliance • buyer intel. By @VametraAI. 🌐 leadnation.app`
- **YouTube description:** `LeadNation — Intelligence for Global Trade. Tutorials, product demos and trade insights for exporters, importers and trade professionals worldwide. A product of Vametra AI Technologies Pvt Ltd. https://leadnation.app`

---

## 6. MOBILE APP ASSETS (React Native / Expo)

Design targets (export from the final vector once approved):
| Asset | Size | File target |
|---|---|---|
| App icon (master) | 1024×1024 | `app_icon.png` (concept ready) |
| Android adaptive — foreground | 432×432 (safe 66%) | mark on transparent |
| Android adaptive — background | solid `#05070f` | — |
| iOS icon | 1024×1024 (no alpha, no rounded corners) | flatten `app_icon` |
| Splash screen | 1284×2778 (portrait) | `splash_screen.png` (concept ready) |
| Notification icon (Android) | 96×96 monochrome white | silhouette of the mark |

**Parity rule:** the app and website must use the **identical** mark, wordmark, palette and tagline. When
the vector logo is finalized, export both web (`/public/brand/` + favicon) and app (`/assets/`) from the same source.

---

## 7. ASSET LOCATIONS
- Web preview assets: `/app/frontend/public/brand/*.png` → `https://leadnation.app/brand/<file>`
- Live social card: `/app/frontend/public/og-default.png`
- Email wordmark: text-based in `/app/backend/emailer.py` (`_shell`)
- **Pending your approval:** replacing the current site nav logo + favicon with the finalized vector.
