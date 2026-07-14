# LeadNation Global Buyer Intelligence Platform — PRODUCTION READINESS REPORT

> **Status:** Legal + Technical + Business validation. **NO production code written** (per instruction).
> **Date:** June 2026 · **Builds on:** `/app/memory/research/` + `/app/memory/research/acquisition/`.
> **This document is the gate.** Phase 1 (Legal) must be approved before any build.

---

# ★ FINAL VERDICT (the one question)

> **Can LeadNation legally and commercially launch a Global Buyer Intelligence Platform using this architecture?**
>
> **YES — with a clearly bounded scope.** LeadNation *can* legally and commercially launch **if and only if** it launches as a **company/entity-intelligence platform built on official, open, and licensed sources**, with **personal data strictly gated**, **source attribution on every record**, and **licensed feeds used within their contracts**.
>
> **It must NOT launch** as: an unrestricted personal-contact database (scraped emails/phones/LinkedIn), a reseller of confidential customs data, or a bulk re-publisher of licensed/competitor databases. Those specific things are the only "NO"s — and each has a compliant alternative below.

**Plain-English summary:** The core of the vision is **green-lit**. ~80% of the product (company identity, trade activity from public/licensed sources, government registrations, trust scoring, evidence) is legally launchable today. The remaining ~20% (personal contacts, confidential customs, scraped gated data) is legal only under specific conditions — which the architecture already accounts for via the lawful-basis gate, provenance ledger, and license registry.

---

# PHASE 1 — LEGAL VALIDATION (must-pass gate)

## §1.1 The three legal tests (applied to every source)
1. **Collect** — may we access/obtain it? (anti-circumvention, ToS, robots)
2. **Store / Use / Monetize** — may we keep, display, and charge for it? (data protection, copyright, database rights, license)
3. **Sector rules** — customs confidentiality, sanctions, e-privacy.

A "yes" to collect does **not** imply yes to store/monetize. This distinction governs everything.

## §1.2 The master distinction: personal vs. non-personal
- **Non-personal** (company name, registry ID, address, HS codes, shipment volumes, ports, industry, aggregate stats): **broadly collectable, storable, displayable, monetizable.** This is the platform core.
- **Personal** (named individuals, personal emails/phones, LinkedIn profiles): triggers **GDPR / UK-GDPR / India DPDP / PIPEDA / PDPA / APPI / PIPL**. Collectable/usable **only** under a documented lawful basis, gated, opt-out-enabled, and segregated.

## §1.3 Answers to the 11 legal questions

**Q1 — Can LeadNation legally collect from each source type?**
| Source type | Collect? | Condition |
|-------------|:---:|-----------|
| Government/company registries | ✅ | Official APIs/open data; EU registries are "high-value datasets" (free, commercial re-use OK) |
| Ministry of Commerce / trade stats | ✅ | Public aggregates; free re-use |
| Customs authorities | ⚠️ | Only where public (US ocean BoL, LATAM, mirror). NOT confidential/air-truck/opted-out |
| Embassy commercial depts | ✅ | Public directories / relationship-based |
| Trade associations / chambers / EPCs | ✅ | Public directories; prefer partnership; ⚠️ respect member-list ToS |
| Trade events / expo lists | ⚠️ | Where ToS permits; prefer organizer partnership |
| Public procurement portals | ✅ | Open govt data (TED/SAM/UNGM); ⚠️ scrape only where no API + ToS permits |
| Company websites | ✅ | robots-compliant; personal data → lawful-basis gate |
| Public APIs | ✅ | Per API agreement/ToS |
| RSS feeds | ✅ | Intended for syndication |
| Open datasets | ✅ | Per open license (mostly attribution) |
| Bill of Lading providers | ✅ (licensed) | Under vendor license; not resell raw restricted rows |
| Licensed commercial providers | ✅ (licensed) | Within contract's display/redistribution terms |

**Q2 — Can LeadNation permanently store this in MongoDB?**
- **Non-personal company/trade/registry data:** ✅ Yes (EU open data explicitly re-usable; no sui-generis block from public bodies).
- **Licensed feed data:** ✅ per license term (often store-while-subscribed; some require deletion on cancellation — track per contract).
- **Personal data:** ⚠️ Store only with lawful basis + retention limit + erasure capability; **EU personal data should be minimized and time-boxed, not "permanent."**
- **Confidential customs data:** ❌ Do not store.

**Q3 — Can LeadNation display this publicly?**
- Non-personal + open-license data: ✅ (with **attribution** where required, e.g. EU high-value datasets, CC-BY).
- Licensed data: ⚠️ display "evidence of existence" per license; usually cannot bulk-republish raw licensed rows publicly.
- Personal data: ⚠️ display minimally, with lawful basis + opt-out; **avoid publishing personal emails/phones on public pages.**

**Q4 — Can LeadNation monetize access?**
- ✅ **Yes** for company/trade intelligence built on open + licensed data. EU Open Data Directive explicitly permits **commercial re-use** of public-sector/registry data (cannot be forced into non-commercial license).
- ⚠️ Licensed feeds: monetize the **derived intelligence** (resolution, trust, evidence), not verbatim resale of the vendor's raw dataset unless the license allows redistribution.

**Q5 — Can LeadNation sell subscriptions?** ✅ Yes — subscriptions to the *intelligence layer* (search, trust scores, verification, alerts) are fully compliant. This is the business model.

**Q6 — What information CANNOT be stored?**
- Confidential customs/manifest data (US air/truck; any consignee who filed confidentiality; India domestic customs rows).
- Personal data without a lawful basis.
- Special-category personal data (health, etc.) — never relevant, never store.
- Data obtained by circumventing access controls (login-gated scraping).
- Bulk copies of a licensed/competitor database beyond license terms (sui-generis DB right applies to *private* DBs).

**Q7 — What should only be cached (not permanently stored)?**
- **Live-query API results** under ToS that forbid storage (e.g., some KYB/registry APIs bill per-call and restrict caching) → short-TTL cache only.
- **VIES VAT validation** → validate live, cache result briefly.
- **Personal contact data** → cache with expiry (decay ~30%/yr), re-verify on access.
- **Sanctions screening results** → cache but re-screen on every surface (daily).

**Q8 — What must always be linked to the original source?**
- **Everything.** Every attribute carries provenance (source URL + timestamp + license). Additionally, **mandatory attribution** for: EU high-value/open datasets, CC-BY licensed data, ITC/UN/World Bank data, and any source whose license requires "indication of source."

**Q9 — What licenses are required?**
- **Free/registration:** UN Comtrade key, Companies House key, SAM.gov (api.data.gov) key, INSEE account, gBizINFO token, ABN GUID, trade.gov key — **API agreements** (accept ToS).
- **Paid commercial licenses:** Volza / ImportGenius / Panjiva / Datamyne (shipment), OpenCorporates (registry gap-fill), email-verification credits.
- **Open licenses (attribution):** most EU/UK/CA/AU/NZ/JP open data (CC-BY or equivalent).

**Q10 — Which countries have GDPR / privacy / database-right restrictions?**
- **GDPR/UK-GDPR (strict, personal data, extraterritorial, up to 4% turnover):** all EU-27 + UK. **CNIL fined KASPR €240k** for LinkedIn scraping → real enforcement.
- **EU sui-generis Database Right:** protects *private* databases (competitors/aggregators) — do not bulk-extract; **does NOT** let public bodies block registry re-use.
- **India DPDP Act 2023:** in force Nov 2025, full enforcement **May 2027**, extraterritorial, up to ₹250 crore — plan compliance now.
- **Others:** Canada PIPEDA + CASL (strict outreach opt-in), Singapore PDPA, Australia Privacy Act/APPs, Japan APPI, South Korea PIPA, UAE/KSA PDPL (emerging), US CCPA/CPRA (state).

**Q11 — Per-source classification** → see §1.4.

## §1.4 SOURCE CLASSIFICATION MATRIX (Allowed / Restricted / Forbidden + obligations)
| Source | Verdict | Commercial licence | Attribution | API agreement | Crawler |
|--------|---------|:---:|:---:|:---:|:---:|
| UK Companies House | ✅ Allowed | No | Recommended | Yes (free key) | n/a (API) |
| INSEE Sirene (FR) | ✅ Allowed | No | Yes | Yes (free acct) | n/a |
| EU registries (high-value datasets) | ✅ Allowed (commercial OK) | No | Yes | per country | n/a |
| Corporations Canada / CID | ✅ Allowed | No | Recommended | Open | n/a |
| gBizINFO / Corporate Number (JP) | ✅ Allowed | No | Recommended | Yes (token) | n/a |
| ABN Lookup (AU) | ✅ Allowed | No | Yes | Yes (GUID) | n/a |
| ACRA (SG) | ✅ open datasets / ⚠️ live=partner | Live API: partner | Yes | Yes | n/a |
| Wathq (SA) | ⚠️ Restricted (gov onboarding) | Agreement | Yes | Yes | n/a |
| Handelsregister (DE) | ⚠️ via licensed 3rd-party | Yes (vendor) | per vendor | vendor | ⛔ raw scrape |
| MCA21 (IN) / SSM (MY) | ⚠️ Restricted (paid docs) | Fees | Yes | ❌ | ⛔ gated |
| UN Comtrade / WITS / WTO | ✅ Allowed | No | **Yes (required)** | Yes (key) | n/a |
| ITC Trade Map | ⚠️ beta API on request | Possibly | **Yes** | Yes | ⛔ |
| US CBP ocean BoL (FOIA) | ✅ Allowed (public) | No (FOIA) or vendor | Recommended | n/a | via FOIA/vendor |
| US air/truck manifests | ⛔ Forbidden (confidential) | — | — | — | ⛔ |
| India domestic customs rows | ⛔ Forbidden (2016 restriction) | — | — | — | ⛔ |
| Mirror BoL via Volza/ImportGenius | ✅ Allowed (licensed) | **Yes** | per licence | Yes | ⛔ scrape vendor |
| Panjiva / Datamyne | ✅ Allowed (licensed) | **Yes (enterprise)** | per licence | Yes | ⛔ |
| TED / SAM.gov / UNGM | ✅ Allowed | No | Recommended | Yes (key/reg) | n/a |
| GeM / AusTender (no API) | ⚠️ Restricted (ToS-dependent) | No | Yes | ❌ | ⚠️ ToS-gated |
| Trade councils / chambers / EPC dirs | ✅ Allowed / ⚠️ ToS | Partner preferred | Yes | ❌ | ⚠️ |
| Expo exhibitor lists | ⚠️ Restricted (ToS) | Partner preferred | Yes | mixed | ⚠️ |
| Company websites | ✅ Allowed (robots) | No | Link back | n/a | ✅ (robots) |
| RSS / sitemaps / trade news | ✅ Allowed | No | Link back | n/a | ✅ |
| VIES (EU VAT) | ✅ Allowed (validate) | No | No | Yes | n/a; **cache only** |
| trade.gov CSL / sanctions lists | ✅ Allowed (must use) | No | Recommended | Yes (key) | n/a |
| OpenCorporates | ✅ Allowed (licensed) | **Yes (paid API)** | Yes | Yes | ⛔ |
| **LinkedIn people / gated marketplaces** | **⛔ Forbidden** (ToS + GDPR) | — | — | Official API only | ⛔ |

## §1.5 The three "NO"s and their compliant alternatives
| Forbidden action | Law/licence | Compliant alternative |
|------------------|-------------|----------------------|
| Scrape LinkedIn/personal contacts at scale | GDPR (CNIL €240k), LinkedIn ToS | Official APIs, buyer self-claim (consent), licensed opted-in contact vendors, role-based emails from company sites under LIA |
| Resell confidential customs / India domestic rows | Customs confidentiality, IN Notification 140/2016 | Use public US ocean BoL + counterpart mirror data (licensed) + statistics |
| Bulk-republish licensed/competitor DB | EU sui-generis DB right, vendor licence | Store derived intelligence + show "evidence of existence"; monetize the analysis layer, not verbatim raw resale |

## §1.6 Phase 1 verdict
**APPROVED to proceed to Phases 2–8, scoped as a company/entity-intelligence platform with a gated personal-data layer.** The architecture in the following phases is designed to *enforce* these legal boundaries structurally (not by policy alone).
