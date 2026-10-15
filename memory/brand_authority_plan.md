# Vametra AI — Brand Authority Plan (entity recognition)

Problem: Google autocorrects "vametra AI" to "camera AI" because it has no confident
entity for the coined word "Vametra". `vametra.com` already resolves correctly.
On-site signals are now complete; the remaining work is off-site corroboration.

Status: NOTHING in Phase 1-4 has been created. User approval required before any
account, listing or submission. No paid options are recommended.

## Shipped on-site (done, verified in production)
- /about entity page (1097 words) with Organization + AboutPage JSON-LD, company
  details table, official channels with rel="me", explicit camera/imaging disambiguation
- Organization JSON-LD site-wide with alternateName ["Vametra","Vametra AI","vametra.com",
  "Vametra AI Technologies Pvt Ltd"]
- WebSite + SoftwareApplication JSON-LD on the HOME PAGE ONLY per Google site-names spec;
  WebSite.name "Vametra AI", alternateName ["Vametra","vametra.com",...]
- Removed false mobile-app claims and a fabricated aggregateRating
- /marketplace and /network set to noindex and removed from the sitemap

## Phase 1 — Free, zero risk: make existing profiles consistent (DO FIRST)
Canonical strings to use verbatim everywhere:
  Brand:        Vametra AI
  Alt brand:    Vametra
  Website:      https://vametra.com
  Legal entity: Vametra AI Technologies Pvt. Ltd.
  Founded:      2025
  HQ:           Ekveera Chowk, Pipeline Rd, Savedi, Ahilyanagar, Maharashtra 414003, India
  Email:        admin@vametra.com
  One-liner:    Vametra AI is an AI-powered global trade intelligence platform for exporters
                and importers — customs duty, HS codes, FTAs, landed cost, demand data and
                verified buyers across 195+ countries.
Actions (user, manual):
1. LinkedIn company page: set legal name, website, founded year, HQ, industry, and paste the
   one-liner. LinkedIn is heavily weighted for company entities.
2. Instagram @vametra_ai: bio must contain "Vametra AI" and the vametra.com link.
3. Keep the LinkedIn vanity URL stable. Currently linkedin.com/company/vametra.com/.
4. Both profiles are already in Organization.sameAs and on /about with rel="me".

## Phase 2 — Free: Google Business Profile (ELIGIBILITY CHECK FIRST)
Google requires EITHER a physical location staffed during stated hours, OR in-person
contact with customers (service-area business). Online-only businesses are NOT eligible.
Vametra AI appears eligible as a service-area business because it sells in-person
consulting (IEC/RCMC/GST registration, export and import consulting) from Ahilyanagar.
Decision needed from user:
  a) Do you meet clients in person or serve them at their premises?  -> eligible
  b) Purely online, no in-person contact?                            -> NOT eligible, skip
If eligible: category "Business Management Consultant" or "Export/Import Company",
hide the address if it is a home office and declare a service area instead.
Verification is by postcard or video. Free.

## Phase 3 — Wikidata: ASSESS, DO NOT FORCE
Honest assessment: Vametra AI most likely does NOT qualify today.
Wikidata notability requires one of:
  1. a sitelink to Wikipedia/Wikivoyage/Wikisource etc., or
  2. a "clearly identifiable conceptual entity" described by at least one SERIOUS AND
     PUBLICLY AVAILABLE reference (independent of the subject), or
  3. structural need to complete other Wikidata statements.
A 2025-founded private company with no independent press coverage fails 1 and 2, and an
item created for SEO reasons is routinely deleted and can look manipulative.
Correct sequence: earn Phase 4 press mentions FIRST, then re-assess.
Do not submit until there are at least 2-3 independent, non-promotional sources.

## Phase 4 — Free, legitimate press and profile opportunities
Ranked by effort-to-value. All free. None created without approval.
1. Crunchbase basic company profile — free, accepts self-submission, widely cited by
   AI systems and often used as a corroborating source.
2. Indian startup directories that accept free listings: StartupIndia (DPIIT) registration
   if the Pvt Ltd is eligible, YourStory / Inc42 company profiles.
3. Trade-body routes, highest credibility for this niche: FIEO membership listing,
   your relevant Export Promotion Council directory, local chamber of commerce. These
   also fit the business and are not SEO-only.
4. Founder-led earned media: Vaibhav Deshmane writing a data-backed guest article for an
   Indian trade/logistics publication. The platform publishes real WITS/OEC analysis, so
   there is genuine substance to pitch rather than a press release.
5. Product directories where the product genuinely belongs: Product Hunt launch, G2 /
   Capterra vendor listing. Free tiers only.
6. GitHub or open-data presence if any part of the HS/tariff tooling can be published.

## Phase 5 — Signals Google reads passively
- Brand query volume: as real users search "vametra" and click vametra.com, Google learns
  the association. Marketing spend should push the exact string "Vametra AI" and the URL.
- Add X/Twitter and YouTube only if they will actually be maintained; dormant profiles do
  not help. When added, put them in lib/brand.js SOCIALS and they propagate to
  Organization.sameAs, the footer, /about and share metadata automatically.
- In GSC, watch Performance > Queries for "vametra" impressions. Rising brand impressions
  are the leading indicator that the autocorrect will stop.

## Expected timeline
Phase 1 is immediate. Phase 2 verification 1-2 weeks. Autocorrect behaviour typically
changes over 4-12 weeks once 2-3 independent sources plus consistent profiles exist.
No code change can shortcut this.
