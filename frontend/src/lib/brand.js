// ─────────────────────────────────────────────────────────────
// LeadNation — SINGLE SOURCE OF TRUTH for brand + social identity.
// Add a new social platform here and it propagates to the Footer,
// Contact page, SEO sameAs / Knowledge Graph and share metadata.
// ─────────────────────────────────────────────────────────────
export const SITE_URL = "https://leadnation.app";
export const BRAND_NAME = "LeadNation";
export const LEGAL_NAME = "Vametra AI Technologies Pvt Ltd";
export const TAGLINE = "Intelligence Beyond Borders";
export const BRAND_ONE_LINER =
  "LeadNation — the AI-powered Global Trade Intelligence platform. Customs duties, HS codes, FTAs, landed cost, expos, market data and trade news for 195+ countries.";

export const EMAIL = "admin@leadnation.app";
export const PHONE = "+91-8237161088";

// key = stable id, order = display order. url is canonical.
export const SOCIALS = [
  { key: "instagram", label: "Instagram", handle: "leadnation.app", url: "https://www.instagram.com/leadnation.app/" },
  { key: "linkedin", label: "LinkedIn", handle: "leadnation-app", url: "https://www.linkedin.com/company/leadnation-app/" },
  // Future: add { key: "twitter", ... }, { key: "youtube", ... } here — everything else updates automatically.
];

// Derived list for schema.org sameAs / OpenGraph profile links.
export const SAME_AS = SOCIALS.map((s) => s.url);

export const social = (key) => SOCIALS.find((s) => s.key === key);
