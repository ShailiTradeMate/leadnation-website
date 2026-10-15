// ─────────────────────────────────────────────────────────────
// Vametra AI — SINGLE SOURCE OF TRUTH for brand + social identity.
// Add a new social platform here and it propagates to the Footer,
// Contact page, SEO sameAs / Knowledge Graph and share metadata.
// ─────────────────────────────────────────────────────────────
export const SITE_URL = "https://vametra.com";
export const BRAND_NAME = "Vametra AI";
export const LEGAL_NAME = "Vametra AI Technologies Pvt Ltd";
export const TAGLINE = "Intelligence Beyond Borders";
export const BRAND_ONE_LINER =
  "Vametra AI — the AI-powered Global Trade Intelligence platform. Customs duties, HS codes, FTAs, landed cost, expos, market data and trade news, with contact-verified buyers across 32 countries.";

export const EMAIL = "admin@vametra.com";
export const PHONE = "+91-8237161088";
export const FOUNDED = "2026";
export const FOUNDER = "Vaibhav Deshmane";
export const HQ = "Savedi, Ahilyanagar, Maharashtra 414003, India";
// Live-verified coverage figures (see /app/memory/verified_claims.md). Never quote "195+".
export const BUYER_COUNTRIES = 32;
export const TARIFF_COUNTRIES = 56;

// key = stable id, order = display order. url is canonical. display = what users see.
export const SOCIALS = [
  { key: "instagram", label: "Instagram", handle: "vametra_ai", display: "@vametra_ai", url: "https://www.instagram.com/vametra_ai/" },
  { key: "linkedin", label: "LinkedIn", handle: "vametra.com", display: "linkedin.com/company/vametra.com", url: "https://www.linkedin.com/company/vametra.com/" },
  // Future: add { key: "twitter", ... }, { key: "youtube", ... } here — everything else updates automatically.
];

// Derived list for schema.org sameAs / OpenGraph profile links.
export const SAME_AS = SOCIALS.map((s) => s.url);

export const social = (key) => SOCIALS.find((s) => s.key === key);
