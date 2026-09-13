// Source transparency — category-level only. Individual organisation / database names are
// never shown on the Verified Buyers surfaces; they are mapped to these category labels.
export const SOURCE_CATEGORIES = [
  { name: "Government & Official Records", tier: "official" },
  { name: "International Trade Data", tier: "official" },
  { name: "Business Registries", tier: "gov" },
  { name: "Public Procurement Records", tier: "gov" },
  { name: "Trade & Industry Records", tier: "directory" },
  { name: "Company-Published Information", tier: "directory" },
  { name: "Compliance & Sanctions Data", tier: "official" },
];

const NAME_MAP = {
  "united nations trade statistics": "International Trade Data",
  "uk government company registry": "Government Business Registries",
  "us government entity registry": "Government Entity Records",
  "eu government procurement records (open data)": "Public Procurement Records",
  "eu government procurement records": "Public Procurement Records",
  "eu government vat validation": "Business & Tax Registries",
  "australian government business register": "Government Business Registries",
  "company-published information": "Company-Published Records",
  "trade fair exhibitor records": "Trade & Industry Records",
  "export promotion council directory": "Trade Promotion Directories",
  "canadian government import records": "Government Trade Records",
  "global company identity registry": "Global Business Identity Data",
  "french government business registry": "Government Business Registries",
};

const CATEGORY_MAP = {
  trade_stats: "International Trade Data",
  registry: "Government Business Registries",
  tenders: "Public Procurement Records",
  tax_id: "Business & Tax Registries",
  website: "Company-Published Records",
  exhibitor: "Trade & Industry Records",
  association: "Trade Promotion Directories",
  customs_bol: "Government Trade Records",
  identity: "Global Business Identity Data",
  sanctions: "Compliance & Sanctions Data",
};

export const mapSourceName = (name, category) => {
  const key = String(name || "").trim().toLowerCase();
  if (NAME_MAP[key]) return NAME_MAP[key];
  if (category && CATEGORY_MAP[category]) return CATEGORY_MAP[category];
  if (/sanction|denied/.test(key)) return "Compliance & Sanctions Data";
  if (/procure|tender/.test(key)) return "Public Procurement Records";
  if (/customs|import|export record/.test(key)) return "Government Trade Records";
  if (/registry|register/.test(key)) return "Government Business Registries";
  if (/trade statistic|comtrade/.test(key)) return "International Trade Data";
  if (/fair|exhibitor|industry/.test(key)) return "Trade & Industry Records";
  if (/website|published/.test(key)) return "Company-Published Records";
  if (/council|association|promotion/.test(key)) return "Trade Promotion Directories";
  return "Government & Official Records";
};

export const mapSourceList = (list = []) => {
  const out = [];
  list.forEach((s) => {
    const label = typeof s === "string" ? mapSourceName(s) : mapSourceName(s?.name, s?.category);
    if (!out.includes(label)) out.push(label);
  });
  return out;
};

export const USAGE_NOTE =
  "Users cannot sell/expose this data, nor can they use this data for monetary benefits by creating a " +
  "website/app that sells buyers' data from our database. It will attract legal issues to the user.";
