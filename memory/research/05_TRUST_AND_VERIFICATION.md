# Deliverables 7 & 8 — Trust Score Proposal + Buyer Verification Framework

---

## Deliverable 8 — Buyer Verification Framework (do this first; Trust Score sits on top)

Verification answers: *"Is this a real, active, reachable commercial entity that plausibly buys/sells what we claim?"* We verify **per attribute**, then roll up.

### The 6 verification dimensions
| Dimension | Question | Strong evidence | Weak/absent |
|-----------|----------|-----------------|-------------|
| **Existence** | Is it a real registered entity? | Government registry match (registry ID, active status) | Only a name on a shipment row |
| **Trade activity** | Does it actually trade? | ≥1 verified BoL/customs record; import history; corridor match | No shipment trace |
| **Recency** | Is it *currently* active? | Shipment/tender/registry event in last 6–12 mo | Last signal >3 yrs |
| **Reachability** | Can a customer reach them? | Verified domain (MX valid), deliverable email, working phone, LinkedIn | Bounced email, dead domain |
| **Corroboration** | Do independent sources agree? | Registry + shipment + web + directory all point to same entity | Single source only |
| **Standing / risk** | Any red flags? | Not on sanctions/denied lists; years in business; council membership | Sanctions hit, dissolved status |

### Verification signal catalogue (mapped to sources from Deliverable 2/3)
- **Government registration:** Companies House / Sirene / Corporations Canada / ACRA / Wathq / ABN / NZBN / Japan Corporate Number → *Existence + Standing*.
- **Import/customs history:** US CBP ocean BoL, Canada CID, mirror data (Volza/Panjiva) → *Trade activity + Recency + corridor/HS match*.
- **Bill of Lading detail:** counterparties, HS, volume, frequency → *Trade activity depth*.
- **Website:** domain age, HTTPS, MX records, address consistency → *Reachability + Existence*.
- **LinkedIn (via API/partner only):** company page, headcount, activity → *Existence + size* (never scraped).
- **Trade events / expos:** exhibitor lists → *Recency + intent*.
- **Trade association / EPC membership:** APEDA/FIEO/MATRADE etc. → *Standing + verification*.
- **Export/import council registration:** IEC (IN), SAM.gov UEI (US) → *Existence*.
- **Years in business:** incorporation date → *Standing*.
- **Email verification:** SMTP/MX check + role vs personal + lawful-basis stamp → *Reachability*.
- **Phone verification:** line validation, country match → *Reachability*.
- **Sanctions/PEP screening:** OFAC/EU/UN/UK/CSL → *Risk gate (hard fail)*.

### Verification tiers (what LeadNation shows the user)
- **Tier 0 — Unverified lead:** name only, single source. *Never* shown as a "buyer"; kept internal.
- **Tier 1 — Registry-verified:** matched to a government registry (exists + legal standing).
- **Tier 2 — Trade-verified:** Tier 1 + confirmed trade activity (shipment/customs/tender) in relevant HS/corridor.
- **Tier 3 — Contact-verified:** Tier 2 + at least one *deliverable, lawful-basis* contact channel.
- **Tier 4 — LeadNation Verified™ (premium):** Tier 3 + multi-source corroboration + recency ≤6 mo + clean sanctions + optional human/QA or buyer-confirmed. This is the flagship, monetizable object.

---

## Deliverable 7 — Trust Score Proposal

### Design principles
1. **Transparent, not black-box.** Every score decomposes into visible factors + provenance (this is the AEO/citability differentiator — an LLM can cite *why*).
2. **Attribute-level → entity-level.** Score each attribute's confidence, then compose.
3. **Time-decayed.** Trust erodes without fresh corroboration.
4. **Calibrated.** Score must correlate with real outcomes (deliverability, response, conversion) and be back-tested.
5. **Hard gates override soft points.** Sanctions/dissolved = capped low regardless of other signals.

### The LeadNation Trust Score (0–100) — factor model
Composite of 6 weighted sub-scores (illustrative starting weights; tune via back-testing):

| Sub-score | Weight | Drivers |
|-----------|:---:|---------|
| **Identity confidence** | 25% | Registry match strength, unique registry ID, address consistency, entity-resolution confidence |
| **Trade evidence** | 25% | # independent shipment/customs records, HS/corridor relevance, volume/frequency |
| **Recency / freshness** | 20% | Age of most recent verified signal (exponential decay, e.g. half-life 12 mo) |
| **Corroboration / source diversity** | 15% | # of *independent* source categories agreeing (registry+shipment+web+directory) |
| **Reachability** | 10% | Deliverable email, valid phone, live domain, LinkedIn presence |
| **Standing & longevity** | 5% | Years in business, council membership, filing compliance |
| **Risk gate (multiplier)** | ×0–1 | Sanctions/PEP/dissolved → multiplier crushes score to a hard cap |

`TrustScore = (Σ weightᵢ · subscoreᵢ) × RiskGate`

### Confidence bands (what users see)
- **90–100 Platinum** — multi-source, fresh, reachable, clean. (Tier 4 territory.)
- **75–89 Verified** — strong identity + trade evidence + a contact.
- **50–74 Probable** — real entity, some trade signal, thin contact/recency.
- **25–49 Weak** — single-source or stale; flagged.
- **0–24 / Gated** — unverified or risk-flagged; not surfaced as a buyer.

### Freshness decay example
`recency_score = 100 · 0.5^(months_since_last_signal / 12)` → a buyer silent 24 months scores ~25 on recency, pulling the composite down and triggering a re-verification job.

### Explainability payload (per buyer)
Every scored buyer ships with a machine + human readable breakdown:
```
TrustScore: 87 (Verified)
  Identity 92  — matched UK Companies House #01234567 (active, inc. 2009)
  Trade    85  — 6 US ocean BoL records, HS 3004, last 2026-04
  Recency  78  — last signal 3 months ago
  Corrob.  80  — registry + 2 shipment sources + website agree
  Reach    70  — domain live, MX valid, role email verified (LI: legit-interest, opt-out ok)
  Standing 88  — 17 yrs, FIEO member
  Risk gate ×1.0 — no sanctions/PEP hits (screened 2026-06-01)
Sources: [12 provenance records with URLs + timestamps]
```
This payload *is* the product's trust moat and its AEO citation surface.

### Anti-gaming & QA
- Weight *independent* sources only (dedupe correlated feeds so one reseller can't inflate corroboration).
- Cap contribution of any single vendor feed.
- Random human-QA sampling on Tier 4 to keep calibration honest.
- User feedback ("bad contact / wrong company") feeds back as negative signal + triggers re-verify.

### Refresh cadence hook
Trust Score recomputes on: (a) any new signal, (b) scheduled source refresh (see `06_ARCHITECTURE.md` §refresh), (c) user feedback, (d) sanctions-list update.
