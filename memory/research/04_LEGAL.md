# Deliverable 6 — Legal Considerations

> Not legal advice. This is an engineering-grade risk map to be validated by qualified counsel per jurisdiction before production ingestion.

## §1. The three legal layers (always separate them)
1. **Can the data be *collected*?** (access/anti-circumvention, e.g. CFAA in US, Computer Misuse in UK).
2. **Can it be *used/stored/sold*?** (data protection: GDPR/UK-GDPR, PDPA, DPDP Act; database rights; contract/ToS).
3. **Are there *sector rules*?** (customs confidentiality, sanctions/export control, e-privacy for outreach).

A "yes" on layer 1 (public/scrapeable) does **not** imply yes on layers 2–3. This is the trap most trade-data vendors quietly sit inside.

## §2. Personal vs. non-personal data — the master distinction
- **Non-personal** (company name, registry ID, HS codes, shipment volumes, ports, aggregate stats): low risk, broadly usable. **~80% of LeadNation's core value lives here.**
- **Personal** (named individuals, personal/role emails tied to a person, phone of a person, LinkedIn profiles): triggers GDPR/PDPA/DPDP. Handle in a **separate, gated pipeline** with lawful basis, retention limits, and opt-out.

**Design principle:** *Company-level first; person-level only with lawful basis.* Never blend them in one uncontrolled store.

## §3. GDPR / UK-GDPR (EU + UK subjects)
- Applies to B2B personal data too (e.g. `jane.doe@acme.de`, job titles).
- **Lawful basis = Legitimate Interest (Art. 6(1)(f))**, not consent, for prospecting — but requires:
  1. Documented **Legitimate Interest Assessment (LIA)** per source/use.
  2. **Necessity** (least-intrusive means).
  3. **Balancing test** (your interest vs. individual rights).
  4. **Transparency** (Art. 14 notice) + easy **opt-out / erasure**.
- **Enforcement is real:** CNIL fined **KASPR €240,000 (2024)** for scraping LinkedIn data without lawful basis/transparency. Fines up to **4% global turnover**.
- **UK DUAA 2025:** new "recognised legitimate interests" is **public-interest only** — does *not* cover commercial B2B lead-gen; still need standard LIA.
- **Action:** build a **Lawful-Basis Engine** that stamps every personal attribute with (source, basis, LIA ref, capture date, retention, opt-out status).

## §4. US
- **hiQ v. LinkedIn:** scraping *public* data does not violate **CFAA** (public sites are "open"). BUT:
  - It can still be **breach of contract** (LinkedIn ToS forbids scraping) → contractual/tort exposure.
  - State privacy laws (CCPA/CPRA etc.) grant deletion/opt-out rights even for B2B in some cases.
- **Customs data:** US ocean BoL is lawfully public via FOIA; using it is fine. Respect consignee **confidentiality opt-outs** (don't resurface data a company has certified confidential).

## §5. Customs / trade-data specific
- **India:** transaction-level customs data restricted since 2016 (Notification 140/2016). Do **not** claim domestic Indian customs rows; mirror data (counterpart country's public manifests) is the compliant route, but recent India mirror data may be **truncated (T2)** and Indian authorities have moved to restrict sharing — monitor and diversify.
- **US consignee opt-out (19 CFR §103.31):** honor it; scrub opted-out parties on refresh.
- **Air/truck manifests (US) are confidential** — never present as public.
- Many countries treat customs data as **confidential business information** — only aggregate stats are public. Selling "named importer" data sourced from confidential feeds is a legal landmine; rely on registries + public manifests + mirror data.

## §6. Sanctions & export control (mandatory)
- Screen every surfaced entity/person against **OFAC SDN, EU consolidated, UN, UK OFSI**, and **trade.gov Consolidated Screening List**.
- Do not facilitate introductions to sanctioned or denied parties; log screening for audit.
- Dual-use goods (HS-linked) may carry export-control flags — surface warnings.

## §7. Database rights & ToS
- EU **sui generis database right** protects substantial extractions from third-party DBs — do not bulk-extract a competitor/aggregator DB.
- License agreements (Volza/Panjiva/etc.) restrict redistribution — respect field-level usage terms; keep a **license registry** mapping each field to what LeadNation may display/resell.

## §8. e-Privacy / outreach (when customers contact buyers)
- Outbound email/SMS is governed by e-Privacy (EU), CAN-SPAM (US), PECR (UK), CASL (Canada — strict opt-in), etc.
- LeadNation should provide **suppression lists, opt-out handling, and per-jurisdiction sending rules** if it ever enables outreach; otherwise clearly position as data provider (customer bears outreach compliance) — but give them the tools.

## §9. Data-protection engineering requirements (build these in)
1. **Provenance ledger** — every attribute: source URL, license, fetch timestamp, method (API/bulk/crawl).
2. **Lawful-basis field** on all personal attributes + LIA document store.
3. **DSAR/erasure workflow** — locate + delete a person across the graph on request.
4. **Retention policy** per data class (e.g., stale personal contact auto-expire).
5. **Geo-partitioning** — EU personal data logically segregated; region-aware processing.
6. **Opt-out registry** (customs confidentiality + individual objections) applied on every refresh.
7. **Audit log** of who accessed what.

## §10. Jurisdiction risk summary
| Jurisdiction | Personal-data regime | Scraping stance | LeadNation posture |
|--------------|----------------------|-----------------|--------------------|
| US | Sectoral + CCPA | Public scraping OK (CFAA) but ToS risk | Use public BoL + registries; API-first |
| EU | GDPR (strict) | LI + LIA required; enforcement active | Company-data led; gate personal data; LIA per source |
| UK | UK-GDPR + DUAA25 | LI required (RLI not for B2B) | Same as EU; leverage Companies House openness |
| India | DPDP Act 2023 | Customs restricted; DPDP consent-heavy | Mirror data + registries; DPDP for personal |
| GCC | PDPL (SA/UAE emerging) | Registries official | Use official CR APIs; localize as PDPL matures |
| Canada | PIPEDA + CASL | Strict outreach opt-in | Great open data (CID); mind CASL for outreach |
| SG/AU/NZ/JP/KR | PDPA/Privacy Act/APPI/PIPA | Official APIs available | API-first; low friction |

## §11. Bottom line
LeadNation can build a **legally durable** product by (a) leading with **company-level + public-sector data**, (b) treating **personal data as a gated, lawful-basis-governed minority**, (c) **licensing** shipment feeds rather than scraping, and (d) baking **provenance + sanctions screening + opt-out** into the core. This compliance posture is itself a *marketing asset* — "the trustworthy trade-data company."
