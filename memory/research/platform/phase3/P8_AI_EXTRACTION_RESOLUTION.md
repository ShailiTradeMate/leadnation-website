# VBIE Phase 3 — Doc 4/6: AI Extraction Pipeline + Entity Resolution
## (Deliverable 5: AI Extraction Architecture · Section 4: AI Extraction · Section 5: Entity Resolution)

> Architecture only. NO code. All AI is grounded + candidate-gated (no auto-trust, no hallucination into the live graph).

---

## SECTION 4 — AI EXTRACTION PIPELINE (the Brain Extraction Engine)

### §4.1 Principle
Turn *any* messy input (PDF, scanned image, HTML, brochure, speaker list) into **validated structured JSON**, with **evidence captured** and a **human/heuristic gate** before promotion. AI *extracts*; it never *invents*.

### §4.2 Universal extraction flow
```
INPUT (PDF/OCR/HTML/CSV/feed)
  → 1. PRE-PROCESS  (text layer? else OCR; language detect; clean)
  → 2. TRANSLATE    (non-English → English working copy; keep original)
  → 3. STRUCTURE-FIRST PARSE (JSON-LD/schema.org/tables) — cheap, high-trust
  → 4. LLM EXTRACT (only for unstructured remainder) → candidate fields + source snippet
  → 5. SCHEMA VALIDATE (types, HS-code sanity, country codes, required fields)
  → 6. CONFIDENCE SCORE (extractor reliability × source trust)
  → 7. EVIDENCE CAPTURE (snippet + source_url + extractor_version → provenance)
  → 8. CANDIDATE QUEUE (Tier 0) — never directly visible
  → 9. RESOLUTION + VERIFICATION + TRUST (Sections 5, and Phase 5 Brain)
```

### §4.3 The three example pipelines (from the prompt), designed
**A. Government PDF → candidate**
```
Gov PDF → PDFConnector(text) or OCRConnector(scanned) → language detect/translate
 → LLM structured extraction (company, reg#, address, product/HS if present)
 → schema validation → confidence → provenance(snippet,url) → Trust Engine → candidate queue
```
**B. Company website → enrichment**
```
HTML (SmartCrawler) → structured-data-first (JSON-LD/OG) → LLM for products/industry/export-capability
 → domain/MX verification → map to entity → provenance → candidate/enrichment
 (personal emails → lawful-basis gate; never invented)
```
**C. Trade event → buyer discovery**
```
Speaker/Exhibitor list (HTML/PDF/OCR) → extract org names → entity match/resolution
 → corroborate with registry → IntentEvent(signal) + provenance(evidence) → candidate
```

### §4.4 AI guardrails (anti-hallucination — hard rules)
1. **Grounded only** — extraction operates on the *provided document*, not the model's world knowledge. Retrieval/extraction, not generation of facts.
2. **Snippet-backed** — every extracted field stores the source text snippet as evidence; no snippet → field dropped.
3. **Schema-validated** — types/enums/HS/country validated; invalid → rejected, not "fixed" by guessing.
4. **Confidence-labeled** — low confidence stays low; surfaced as "unverified."
5. **No invented contacts** — AI never fabricates emails/phones/people.
6. **Candidate-gated** — AI output enters Tier 0; promotion needs corroboration + verification.
7. **Cost guard** — structure-first parsing always attempted before LLM; LLM is the fallback, budgeted per night.
- LLM access via the **Emergent LLM key** (per platform integration rules).

### §4.5 Translation pipeline
Detect language → translate working copy (keep original for provenance) → extract on English copy → store both. Handles JP/DE/FR/AR/TH/VI/KO sources. Company legal names kept in original + romanized.

---

## SECTION 5 — ENTITY RESOLUTION (one Buyer ID per real company)

### §5.1 Problem
"ACME Corp", "ACME CORPORATION", "Acme Corp Pvt Ltd", "アクメ", "Acme GmbH" across different sources/languages/addresses must collapse into **one canonical Buyer ID** — or stay distinct when genuinely different.

### §5.2 Resolution pipeline
```
candidate → 1. NORMALIZE (case, legal-suffix strip, transliterate, address standardize)
          → 2. BLOCKING (candidate keys: registry_id, VAT/VIES, domain, name-country n-gram)
          → 3. PAIRWISE MATCH (feature scoring)
          → 4. DECISION (merge / distinct / review)
          → 5. MERGE (canonical id, union attributes+provenance, reversible)
          → 6. RE-SCORE Trust
```

### §5.3 Matching features & weights (start; tune with labeled data)
| Feature | Signal | Weight |
|---------|--------|:--:|
| Exact registry_id / VAT / ABN / UEI match | decisive | ★★★★★ (auto-merge) |
| Verified domain match | very strong | ★★★★☆ |
| Fuzzy legal-name (Jaro-Winkler/Levenshtein, suffix-normalized) | strong | ★★★☆☆ |
| Transliterated/translated name match | strong (cross-language) | ★★★☆☆ |
| Address proximity (geocode + fuzzy) | medium | ★★☆☆☆ |
| Shared HS/corridor/counterparty | supporting | ★★☆☆☆ |
| Shared phone/email (verified) | supporting | ★★☆☆☆ |

### §5.4 Decision thresholds
- **Strong key match** (reg_id/VAT/ABN) → **auto-merge**.
- **Score ≥ high threshold** → merge.
- **Mid band** → **human-QA queue** (admin review).
- **Below** → distinct entities.

### §5.5 Merge operation (safe + reversible)
- Choose surviving canonical Buyer ID (prefer strongest registry identity).
- **Union attributes**, keeping *all* provenance from both; conflicting values coexist with confidences (higher-trust/fresher shown primary).
- Losers → `status=merged`, `merged_into=survivor`; record in `match_decisions` (reversible for audit).
- Re-run Trust Score post-merge.

### §5.6 Cross-language & abbreviation handling
- Multilingual name index (original + romanized + translated).
- Legal-suffix dictionary per country (Ltd/GmbH/SARL/Pvt Ltd/K.K./Pte Ltd…) stripped for comparison, retained for display.
- Abbreviation/alias table ("Intl"→"International", "&"→"and").

### §5.7 Model evolution
Start rules/heuristics (transparent, debuggable) → graduate to an ML matcher trained on confirmed merges + human-QA labels + user "wrong company" feedback. Every decision remains logged & explainable (feeds Brain, Phase 5).
