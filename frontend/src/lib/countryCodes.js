import { COUNTRY_OPTIONS } from '@/data/geo';
// Keep the existing ISO/dial/name contract and E.164 conversion unchanged.
export const COUNTRY_CODES = COUNTRY_OPTIONS.map(c => ({ ...c, iso: c.code }));

export const CC_BY_ISO = COUNTRY_CODES.reduce((m, c) => { m[c.iso] = c; return m; }, {});

// Build an E.164 number from a dial code + a (possibly messy) national number.
// Strips spaces/dashes and any leading zeros from the national part. Empty in → empty out.
export function toE164(dial, national) {
  const d = (national || "").replace(/\D/g, "").replace(/^0+/, "");
  return d ? `${dial}${d}` : "";
}
