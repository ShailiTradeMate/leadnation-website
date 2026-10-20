// Part 6 keyword map for detail templates — one primary keyword per page, H1 contains it verbatim.
const B = "Vametra AI";

export const SERVICE_SEO = {
  "iec-registration": { kw: "iec code registration process", title: `IEC Code Registration Process 2026: Steps, Fees | ${B}`, h1: "IEC code registration process — documents, fees and timeline" },
  "rcmc-registration": { kw: "rcmc certificate apply online", title: `RCMC Certificate Apply Online: Council & Docs | ${B}`, h1: "RCMC certificate apply online — which council, what documents" },
  "gst-registration": { kw: "gst for exporters", title: `GST for Exporters: LUT, Refunds, Registration | ${B}`, h1: "GST for exporters — LUT, zero-rated supply and refunds" },
  "company-registration": { kw: "company registration for export business", title: `Company Registration for Export Business India | ${B}`, h1: "Company registration for export business — structure to IEC" },
  "udyam-registration": { kw: "udyam registration for exporters", title: `Udyam MSME Registration for Exporters: Docs, Benefits | ${B}`, h1: "Udyam registration for exporters — documents, benefits and process" },
  "business-website": { kw: "export business website", title: `Export Business Website: Build to Win Buyers | ${B}`, h1: "Export business website that buyers trust" },
  "export-consulting": { kw: "export consultant india", title: "Export Consultant India: Data-Backed Market Entry | Vametra", h1: "Export consultant India — data-backed market entry" },
  "import-consulting": { kw: "import consultant india", title: "Import Consultant India: Duty, Sourcing, Clearance | Vametra", h1: "Import consultant India — duty, sourcing and clearance" },
  "compliance-consulting": { kw: "trade compliance consulting", title: `Trade Compliance Consulting: Origin, CBAM | ${B}`, h1: "Trade compliance consulting — rules of origin to sanctions" },
  "market-entry": { kw: "export market entry strategy", title: `Export Market Entry Strategy: Pick the Market | ${B}`, h1: "Export market entry strategy built on duty and demand data" },
  "product-sourcing": { kw: "supplier sourcing service", title: `Supplier Sourcing Service: Verified Makers | ${B}`, h1: "Supplier sourcing service — verified Indian manufacturers" },
  "buyer-discovery-service": { kw: "buyer discovery service", title: `Buyer Discovery Service: Verified Importers | ${B}`, h1: "Buyer discovery service — evidence-backed importers" },
};

// Search-friendly short forms for long official names (titles must stay ≤60 chars).
const SHORT = {
  "United Arab Emirates": "UAE", "United States of America": "USA", "United States": "USA",
  "United Kingdom": "UK", "Textiles & Apparel": "Textiles", "Cotton Textiles & Apparel": "Cotton Textiles",
  "Engineering Goods & Machinery": "Engineering Goods", "Food Processing": "Food Processing",
};
const short = (n) => SHORT[n] || n;

export const countrySeo = (name) => ({
  title: clampTitle(`${short(name)} Trade Profile: Tariffs, Imports, Buyers | Vametra AI`),
  h1: `${short(name)} trade profile — tariffs, imports and verified buyers`,
});

export const corridorSeo = (to) => ({
  title: clampTitle(`Export from India to ${short(to)}: Duty, FTA, Shipping | Vametra AI`),
  h1: `Export from India to ${short(to)} — duty, FTA and shipping`,
});

export const productSeo = (name) => ({
  title: clampTitle(`${short(name)} Export from India: HS Code, Duty, Buyers | Vametra AI`),
  h1: `${short(name)} export from India — HS code, duty and buyers`,
});

export const industrySeo = (name) => ({
  title: clampTitle(`${short(name)} Exports from India: Trade Profile | Vametra AI`),
  h1: `${short(name)} exports from India — markets, duty and buyers`,
});

export const courseSeo = (title) => ({
  title: clampTitle(`${title}: Free Course for Exporters | Vametra AI`),
  h1: `${title} — free course`,
});

// Google truncates around 60 chars; keep the keyword at the front so nothing important is cut.
export function clampTitle(t) {
  if (t.length <= 60) return t;
  const s = t.replace(" | Vametra AI", " | Vametra");
  if (s.length <= 60) return s;
  const bare = s.replace(/ \| Vametra$/, "");
  return bare.length <= 60 ? bare : bare.replace(/: [^:]+$/, "");
}
