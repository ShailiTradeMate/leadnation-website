# LeadNation Verified Buyer Acquisition System — R&D (Highest Priority)

> **Status:** Research only. No production code, API, UI, or backend changes.
> **Date:** June 2026 · **Builds on:** `/app/memory/research/` (Buyer Discovery program).
> **Mission:** Every legal, authentic, scalable way to acquire verified buyers worldwide, and a pipeline that gets smarter every night — *without* relying on users creating accounts.

## Deliverable → Document map
| # | Deliverable | Doc |
|---|-------------|-----|
| 1 | Complete Buyer Acquisition Strategy | `A1_ACQUISITION_STRATEGY.md` |
| 2 | Source Matrix (all countries) | `A2_SOURCE_MATRIX.md` |
| 3 | API Matrix | `A2_SOURCE_MATRIX.md` §API |
| 4 | Government Source Matrix | `A2_SOURCE_MATRIX.md` §Gov |
| 5 | Commercial Data Provider Matrix | `A2_SOURCE_MATRIX.md` §Commercial |
| 6 | Crawling Strategy | `A3_CRAWLING_LEGAL.md` §Crawl |
| 7 | Legal Strategy | `A3_CRAWLING_LEGAL.md` §Legal |
| 8 | Database Design | `A4_DATABASE_DESIGN.md` |
| 9 | AI Verification Pipeline | `A5_PIPELINE_TRUST_REFRESH.md` §Pipeline |
| 10 | Trust Score Integration | `A5_PIPELINE_TRUST_REFRESH.md` §Trust |
| 11 | Refresh Strategy | `A5_PIPELINE_TRUST_REFRESH.md` §Refresh |
| 12 | MVP Recommendation | `A6_MVP_EFFORT_COST.md` §MVP |
| 13 | Estimated implementation effort | `A6_MVP_EFFORT_COST.md` §Effort |
| 14 | Cost analysis | `A6_MVP_EFFORT_COST.md` §Cost |
| 15 | Final recommendation | `A6_MVP_EFFORT_COST.md` §Final |

## One-line strategy
> **Acquire buyers from free/official sources first (registries + customs + stats + procurement), license shipment data to fill blind corridors, and let an autonomous nightly pipeline resolve → verify → score → attribute every buyer. The product is not the data — it is the *verified, evidenced, continuously-refreshed buyer identity*.**

## The 7-question rubric (answered for every source in `A2`)
1. Official? 2. Trustworthy? 3. Free? 4. API? 5. Crawl legal? 6. Downloadable? 7. Fields (Company/Website/Email/Country/Products/HS/Import-hist/Export-hist/Certs/Reg#/Phone/Address/Industry) · +8 Refresh · +9 Legal restrictions · +10 Commercial licensing.
