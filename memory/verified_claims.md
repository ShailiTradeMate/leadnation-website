# Verified platform numbers (live production API, 2026-06)

Use ONLY these in public copy. Each was read from a live endpoint.

| Claim | Value | Source endpoint / evidence |
|---|---|---|
| HS codes indexed | 5,606 | /api/trade-intel/hs-directory -> total 5606, "WCO HS 2022 nomenclature (via OEC/BACI directory)" |
| HS chapters | 96 | /api/trade-intel/hs-chapters -> count 96 |
| Reporting countries with live applied tariffs | 56 | /api/duty/countries -> total 56, "World Bank WITS / UNCTAD TRAINS reporters" |
| Published product-market export guides | 392 | sitemap count of /export/*/to/* |
| Product hubs | 8 | sitemap count of /export/<product> |
| Regional hubs | 5 | sitemap count of /regions/<slug> |
| Machine-readable answer documents | 413 | /api/answers/index -> total 413 |
| Contact-verified buyer records | 30,821 | /api/buyers/meta -> total 30821 (PUBLIC_Q = has contact) |
| Countries with buyer records | 32 | /api/buyers/meta -> len(countries) 32 |
| Sectors with buyer records | 21 | /api/buyers/meta -> len(sectors) 21 |
| Total indexable URLs | 974 | /api/sitemap.xml |
| Country profiles written | 5 | /api/country-profiles -> len 5 |

## RESOLVED 2026-10-15 — "195+ countries" removed everywhere
All 22 occurrences replaced with "contact-verified buyers across 32 countries" (buyer context) or
"56 tariff-reporting countries" (tariff context). `brand.js` exports BUYER_COUNTRIES=32, TARIFF_COUNTRIES=56.
Still unverified on Home hero: "32K HS Codes" (live: 5,606) and "1.2M Data points" — owner has not asked to change.

Suggested honest replacements:
  "195+ countries"                -> "56 tariff-reporting countries"
  "195+ markets"                  -> "392 published product-market guides"
  Home <Stat value="195+" label="Countries" /> -> value "30,821" label "Verified buyers"
                                   or value "5,606" label "HS codes"
  About STATS Globe row           -> "30,821 contact-verified buyer records across 32 countries"
