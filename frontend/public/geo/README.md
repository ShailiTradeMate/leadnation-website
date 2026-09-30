# Location data

Generated from country-state-city 3.2.1 (Open Database License, see LICENSE).
Upstream: https://github.com/harpreetkhalsagtbit/country-state-city
250 countries/territories, 4,963 subdivisions and 148,038 city records.

Regenerate with `node scripts/generate-geography.cjs` from frontend/.
Countries are shared by every location selector. Each country's states/cities are
loaded separately on demand; the complete city database is NOT in the JS bundle.
Names for PS/VA/TR/CZ are normalized; VA uses +39 rather than the unused +379.
Coverage is not a claim to list every village or municipality worldwide. State
and city pickers allow custom values, including during offline/load failures.