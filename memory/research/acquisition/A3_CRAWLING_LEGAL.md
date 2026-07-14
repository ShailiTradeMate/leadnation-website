# Deliverables 6 & 7 — Crawling Strategy + Legal Strategy

> Extends `/app/memory/research/04_LEGAL.md`. Not legal advice; validate with counsel per jurisdiction.

---

## Deliverable 7 — LEGAL STRATEGY (the guardrail that makes acquisition durable)

### §1. Five operating principles
1. **Company-data first, personal-data gated.** ~80% of buyer value is non-personal (Co, Reg#, HS, Addr, trade activity) → low risk. Personal data (named people, personal emails/phones) routes through a lawful-basis pipeline only.
2. **API/license before crawl.** Prefer official APIs and licensed feeds; crawling is a last resort with legal sign-off per domain.
3. **Provenance on every field.** Source URL + license + timestamp + method stored for every attribute → both defensible and citable.
4. **Honor opt-outs & confidentiality.** US consignee confidentiality (19 CFR §103.31), GDPR objection/erasure, individual opt-out — applied on *every* refresh.
5. **Screen everything.** Sanctions/PEP screening (OFAC/EU/UN/UK + trade.gov CSL) as a hard gate before a buyer is ever surfaced.

### §2. Lawful basis by data class
| Data class | Example | Basis | Notes |
|------------|---------|-------|-------|
| Non-personal company | Co, Reg#, HS, ports, volumes | Legitimate business use | Broadly usable globally |
| Public registry personal | director name in Companies House | Legitimate interest + public-source | Transparency notice; region-aware |
| Contact personal (EU/UK) | jane@acme.de | **Legitimate Interest + documented LIA** | Opt-out + Art.14 notice; CNIL fined KASPR €240k |
| Contact personal (US) | US business email | LI (CCPA opt-out rights) | Honor deletion requests |
| Contact personal (IN) | IN personal data | DPDP Act 2023 (consent-leaning) | Localize as rules finalize |
| Customs named party | US consignee | Public (FOIA) | Respect confidentiality certifications |

### §3. Jurisdiction posture (acquisition-specific)
- **EU/UK:** registry + stats + TED led; personal contacts only via LIA; segregate EU personal data.
- **US:** exploit public ocean BoL + SAM.gov freely; ToS-aware on LinkedIn (don't scrape); honor CCPA.
- **India:** never claim domestic customs rows (2016 restriction); use mirror data + registries; DPDP for personal.
- **GCC:** official CR APIs (Wathq) + GCC-Stat; localize as PDPL matures.
- **CA/AU/NZ/SG/JP/KR:** API-first, low friction; mind CASL (Canada outreach opt-in).

### §4. Contract/DB-rights strategy
- Maintain a **License Registry**: each field ↔ what LeadNation may store / display / resell.
- Never bulk-extract a competitor/aggregator DB (EU sui generis DB right + ToS).
- Licensed feeds (Volza etc.): respect redistribution limits; display evidence without re-selling raw restricted rows verbatim.

### §5. Compliance-as-a-feature
Turn compliance into marketing: "Every LeadNation buyer carries evidence + source attribution; personal data handled under documented lawful basis; sanctions-screened." This is a *trust differentiator* against opaque BoL resellers.

---

## Deliverable 6 — CRAWLING STRATEGY

### §1. The crawl decision tree (per source)
```
Official API?            → YES → use API (stop)
   │ NO
Bulk/open dataset?       → YES → download (stop)
   │ NO
Licensed feed available? → YES → license (stop)
   │ NO
Public + ToS permits reuse + no gated personal data? → YES → crawl (with guardrails)
   │ NO
Partnership/data-sharing agreement? → pursue
   │ else → DO NOT ACQUIRE
```

### §2. Where crawling is appropriate (✅) vs. not (⛔)
- ✅ Company public websites (contact/about, robots-compliant) — reachability & enrichment.
- ✅ Trade news / press via **RSS + sitemaps** (preferred over HTML scraping).
- ✅ Expo/exhibitor lists where ToS permits (prefer organizer partnership).
- ⚠️ Gov portals without API (GeM, AusTender, some registries) — check ToS; many permit public-data reuse; rate-limit hard.
- ⚠️ Germany Handelsregister — use licensed 3rd-party API instead of raw scrape.
- ⛔ LinkedIn people/profiles, gated marketplaces (Alibaba/IndiaMART behind auth), paywalled registries, competitor vendor sites.

### §3. Crawler engineering guardrails
- Respect `robots.txt` + `crawl-delay`; declare an honest User-Agent with contact URL.
- Per-domain rate caps; exponential backoff; auto-halt on 403/429.
- Prefer **structured endpoints** (RSS, sitemap.xml, JSON-LD embedded in pages) over brittle HTML.
- **Provenance capture**: store source URL + fetch timestamp + parser version for every extracted field.
- **Personal-data quarantine**: any personal field extracted goes to the lawful-basis pipeline, never the general store.
- **Politeness & caching**: cache aggressively; never re-crawl unchanged pages (ETag/Last-Modified).
- **Legal gate**: a domain cannot be crawled until it's on an approved allowlist (ToS reviewed).
- Residential/rotating proxies only where genuinely public & permitted (avoid using proxies to defeat access controls — that risks CFAA/anti-circumvention exposure).

### §4. LLM-assisted extraction (for unstructured sources)
- Use LLM (Emergent key) to convert news articles / expo PDFs / press releases into structured `IntentEvent` / `ContactAttribute` candidates.
- **Never auto-trust**: LLM output is a *candidate* requiring corroboration + validation heuristics before promotion beyond Tier 0.
- Capture the source passage as evidence for provenance.

### §5. Anti-patterns to avoid
- Logging into a site to scrape gated data (contract + anti-circumvention risk).
- Harvesting personal emails at scale without lawful basis (GDPR fines).
- Presenting scraped, unverified rows as "buyers" (brand + legal risk).
- Ignoring opt-out/confidentiality on refresh (regulatory risk).
