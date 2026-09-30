import countries from './countries.json';

// ISO identifiers for APIs; names for existing profile/event contracts.
export const COUNTRY_OPTIONS = countries;
export const COUNTRIES = countries.map(c => c.name);
const aliases = {
  usa: 'US', 'united states of america': 'US', uk: 'GB', uae: 'AE',
  'korea, republic of': 'KR', 'korea, democratic people\'s republic of': 'KP',
  'russian federation': 'RU', 'viet nam': 'VN', 'iran, islamic republic of': 'IR',
  'türkiye': 'TR', czechia: 'CZ', 'holy see': 'VA', 'vatican city state (holy see)': 'VA',
  'palestinian territory occupied': 'PS', 'palestine, state of': 'PS',
};
export const countryCode = value => {
  const key = String(value || '').trim().toLowerCase();
  return aliases[key] || countries.find(c => c.code.toLowerCase() === key || c.name.toLowerCase() === key)?.code || '';
};

// Preserve API-specific names (e.g. UAE) when adding missing countries to filters.
export const countryFilterOptions = (existing = []) => {
  const values = new Map(existing.map(value => [countryCode(value) || value, value]));
  return countries.map(c => ({ label: c.name, value: values.get(c.code) || c.name }))
    .concat(existing.filter(v => !countryCode(v)).map(v => ({ label: v, value: v })));
};

const cache = new Map();
export const loadLocalities = country => {
  const code = countryCode(country);
  if (!code) return Promise.resolve({ states: [], cities: [] });
  if (!cache.has(code)) {
    cache.set(code, fetch(`/geo/${code}.json`).then(r => {
      if (!r.ok) throw new Error('Location list unavailable');
      return r.json();
    }).catch(error => { cache.delete(code); throw error; }));
  }
  return cache.get(code);
};