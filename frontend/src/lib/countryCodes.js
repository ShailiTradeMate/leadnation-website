// Country dial codes for the mobile-number selector. Value stored is the ISO code;
// dial + name are derived. Numbers are normalised to E.164 for the shared users record.
// Ordered: flagship (India) first, then the VBIE priority markets, then the rest.
export const COUNTRY_CODES = [
  { iso: "IN", name: "India", flag: "🇮🇳", dial: "+91" },
  { iso: "US", name: "United States", flag: "🇺🇸", dial: "+1" },
  { iso: "CA", name: "Canada", flag: "🇨🇦", dial: "+1" },
  { iso: "GB", name: "United Kingdom", flag: "🇬🇧", dial: "+44" },
  { iso: "AE", name: "United Arab Emirates", flag: "🇦🇪", dial: "+971" },
  { iso: "DE", name: "Germany", flag: "🇩🇪", dial: "+49" },
  { iso: "FR", name: "France", flag: "🇫🇷", dial: "+33" },
  { iso: "NL", name: "Netherlands", flag: "🇳🇱", dial: "+31" },
  { iso: "SG", name: "Singapore", flag: "🇸🇬", dial: "+65" },
  { iso: "JP", name: "Japan", flag: "🇯🇵", dial: "+81" },
  { iso: "AU", name: "Australia", flag: "🇦🇺", dial: "+61" },
  { iso: "MX", name: "Mexico", flag: "🇲🇽", dial: "+52" },
  { iso: "IT", name: "Italy", flag: "🇮🇹", dial: "+39" },
  { iso: "ES", name: "Spain", flag: "🇪🇸", dial: "+34" },
  { iso: "BE", name: "Belgium", flag: "🇧🇪", dial: "+32" },
  { iso: "CH", name: "Switzerland", flag: "🇨🇭", dial: "+41" },
  { iso: "SA", name: "Saudi Arabia", flag: "🇸🇦", dial: "+966" },
  { iso: "QA", name: "Qatar", flag: "🇶🇦", dial: "+974" },
  { iso: "OM", name: "Oman", flag: "🇴🇲", dial: "+968" },
  { iso: "KW", name: "Kuwait", flag: "🇰🇼", dial: "+965" },
  { iso: "MY", name: "Malaysia", flag: "🇲🇾", dial: "+60" },
  { iso: "TH", name: "Thailand", flag: "🇹🇭", dial: "+66" },
  { iso: "VN", name: "Vietnam", flag: "🇻🇳", dial: "+84" },
  { iso: "ID", name: "Indonesia", flag: "🇮🇩", dial: "+62" },
  { iso: "KR", name: "South Korea", flag: "🇰🇷", dial: "+82" },
  { iso: "NZ", name: "New Zealand", flag: "🇳🇿", dial: "+64" },
  { iso: "BD", name: "Bangladesh", flag: "🇧🇩", dial: "+880" },
  { iso: "LK", name: "Sri Lanka", flag: "🇱🇰", dial: "+94" },
  { iso: "NP", name: "Nepal", flag: "🇳🇵", dial: "+977" },
  { iso: "BT", name: "Bhutan", flag: "🇧🇹", dial: "+975" },
  { iso: "CN", name: "China", flag: "🇨🇳", dial: "+86" },
];

export const CC_BY_ISO = COUNTRY_CODES.reduce((m, c) => { m[c.iso] = c; return m; }, {});

// Build an E.164 number from a dial code + a (possibly messy) national number.
// Strips spaces/dashes and any leading zeros from the national part. Empty in → empty out.
export function toE164(dial, national) {
  const d = (national || "").replace(/\D/g, "").replace(/^0+/, "");
  return d ? `${dial}${d}` : "";
}
