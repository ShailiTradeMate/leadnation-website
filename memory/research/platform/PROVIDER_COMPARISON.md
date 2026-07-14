# Licensed Provider Comparison — Volza vs ImportGenius vs Panjiva vs Datamyne
## For target corridors: USA · Canada · UK · UAE · Germany · Japan · Australia

> **Purpose:** Reference for a **future** licensing decision (NOT now). LeadNation launches free-first; this informs which module(s) to enable later, per corridor. Prices are 2026 research; confirm under quote before purchase.

## §1. Why we even need a licensed provider
Our target corridors split into two groups:
- **Public/free-data corridors (no license needed):** 🇺🇸 USA (CBP ocean BoL), 🇨🇦 Canada (CID). We get named buyers here for **$0**.
- **Confidential-import corridors (need mirror BoL):** 🇬🇧 UK, 🇩🇪 Germany, 🇯🇵 Japan, 🇦🇺 Australia, 🇦🇪 UAE — imports are not public, so named importers come from **counterpart-country mirror data** sold by licensed providers (or from registries+procurement, which we already do free).

So a license only *accelerates* the 5 confidential corridors — it is an enhancement, not a foundation.

## §2. Head-to-head (2026)
| Dimension | Volza | ImportGenius | Panjiva (S&P) | Datamyne (Descartes) |
|-----------|-------|--------------|---------------|----------------------|
| Countries covered | **203–209** | 23–25 (US-centric) | 100+ (US-strong) | 190+ |
| Entry price/yr | **~$1,500** (transparent) | ~$1,794 ($149–399/mo) | Custom (~$5k–25k+) | Custom (~$15k+) |
| Pricing transparency | ★★★★★ | ★★★★ | ★ | ★ |
| API access | ✅ (paid tiers) | ✅ | ✅ (enterprise) | ✅ (enterprise) |
| Contact-level data | ✅ (decaying) | partial | ✅ | limited |
| Best region | Emerging mkts + broad | US + LATAM | US + Americas + risk analytics | Asia-Pacific + LATAM |

## §3. Corridor-by-corridor coverage (the decision that matters)
| Corridor | Volza | ImportGenius | Panjiva | Datamyne | LeadNation note |
|----------|:---:|:---:|:---:|:---:|-----------------|
| 🇺🇸 USA | ✅ | ✅ (deep) | ✅ (deep) | ✅ (deep) | **No license needed** — free CBP ocean BoL |
| 🇨🇦 Canada | ✅ | ✅ | ✅ | ✅ | **No license needed** — free CID |
| 🇬🇧 UK | ✅ | limited | ✅ | ✅ | Free registry+procurement first; license optional |
| 🇩🇪 Germany | ✅ | limited | ✅ | ✅ (strong EU) | Mirror needed for import names; Volza/Datamyne best |
| 🇯🇵 Japan | ✅ | ❌/limited | ✅ | ✅ (strong APAC) | **Datamyne or Volza** (APAC depth) |
| 🇦🇺 Australia | ✅ | ❌/limited | ✅ | ✅ (strong APAC) | **Datamyne or Volza**; ImportGenius weak |
| 🇦🇪 UAE | ✅ | ❌ | ✅ | ⚠️ (MENA broader, not explicit) | **Volza or Panjiva** (Middle East) |

## §4. Fit assessment for LeadNation's 7 corridors
- **Volza** — best single-module fit: covers **all 7** corridors, transparent ~$1,500 entry, has contacts. Weakness: freshness/accuracy questioned; India T2 truncation. → **Recommended default module IF/when we license.**
- **Datamyne** — best for **Japan + Australia + Germany** (APAC/EU depth) but enterprise pricing (~$15k+). → Consider only if APAC becomes a priority corridor.
- **Panjiva** — best analytics + covers all 7 incl. UAE, but custom enterprise cost (3–30× Volza). → Enterprise phase / risk-intelligence upsell.
- **ImportGenius** — **US/LATAM only**; weak on Japan/Australia/UAE. → Not suitable for our confidential-corridor gap (we already have US free). → **Deprioritize.**

## §5. Recommendation (for the FUTURE decision — not now)
1. **Launch with zero license.** Free sources cover USA + Canada + all registries + procurement.
2. When a paying customer needs a confidential corridor (DE/JP/AU/UAE/UK) → enable **Volza** first (broadest, cheapest, transparent) as the pluggable `MirrorBoLProvider` adapter.
3. If **Japan/Australia** demand grows → add **Datamyne** adapter for APAC depth.
4. Reserve **Panjiva** for enterprise/risk-analytics tier.
5. Skip **ImportGenius** (US-only overlaps our free data).
6. Keep all four behind the **provider-agnostic interface** so switching costs are near-zero and pricing stays negotiable.

## §6. Provider-agnostic module design (so we never get locked in)
```
interface MirrorBoLProvider:
  search(corridor, hs, date_range) -> normalized ShipmentEvent[]
adapters: VolzaAdapter · ImportGeniusAdapter · PanjivaAdapter · DatamyneAdapter
config: sources_seed.json → each provider is a source with active:false until licensed
```
Enable/disable per corridor via the `sources` registry `active` flag + a license entry in the License Registry. No code change to switch providers — only config.
