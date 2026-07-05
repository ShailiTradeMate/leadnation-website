# LeadNation — ROADMAP (Volumes 2, 3, 4 + Backlog)

> Rule: Volume 1 is COMPLETE and must NOT be redesigned. Everything below EXTENDS the
> existing architecture. Reuse the existing LeadNation Brain (do NOT create another AI).
> Every new module belongs to a Trade Project, feeds the Reactive Computation Graph,
> integrates with the Brain, and flows into the downloadable PDF. No standalone modules.

## Owner
Vaibhav Deshmane · Vametra AI Technologies Pvt Ltd

---

## P1 BACKLOG (from user snip — near-term, independent of Volumes)
- [ ] **Razorpay wiring for India** — blocked on user API keys. Gateway toggle + pricing already in the Pricing Engine; just wire checkout/webhook when keys arrive.
- [ ] **My Reports history + shareable public/private links with expiry** — store generated reports per project; shareable link with visibility + TTL.
- [x] **Legal pages** — DONE (2026-07-05): Privacy, Terms, Cookie, Disclaimer, Refund at `/legal/*` (international scope, reusable links in footer/signup/checkout).
- [ ] **Activate Analytics scaffolding** — GA4 / GTM / Clarity / Meta Pixel via `.env` (scaffold already present in `components/Analytics.jsx`).

---

## VOLUME 2 — TRADE SIMULATION & DECISION ENGINE  (foundational, HIGH priority)
Each Trade Project becomes a Digital Twin; everything recalculates instantly.
- **Phase 2A — DONE (2026-07-05)** — Digital Twin, Scenario Builder (+compare/merge/duplicate/archive/versioning), Trade Score Engine (8 explainable scores), Decision Engine layer, Universal Audit Trail (events), Live Data Adapter framework, Brain recommendations, Volume-2 PDF integration (scores/scenarios/decision/Report ID/QR). Verified iteration_24 (19/19 backend).
- **Phase 2B — Monte Carlo Simulation + Sensitivity Analysis**
  - Monte Carlo: FX, freight, duty, delay, commodity price, demand, volatility → Best/Expected/Worst + probability + confidence.
  - Sensitivity: most sensitive variable, highest cost/risk/profit impact; Brain explains.
- **Phase 2C — Trade Recommendation Engine + Risk Simulation + Trade Forecast**
  - Recommendations: better Incoterm/currency/route/mode/pricing/timing/buyer/supplier (Brain, continuous).
  - Risk Simulation: political, currency, weather, compliance, supplier, buyer, port congestion, geopolitical, sanctions, disaster, container, banking, insurance.
  - Forecast: 30/90/180/365-day market/profit/demand/risk (Brain).
- **Phase 2D — Interactive World Map + PDF integration for Volume 2**
  - Heatmaps: routes, risk, demand, growth, opportunities.
  - PDF: simulation results, scenario comparison, twin, risk, recommendations, forecast, sensitivity, exec summary, charts.

## VOLUME 3 — GLOBAL TRADE INTELLIGENCE NETWORK
- **3A** Live Data Adapters: commodity, FX, freight, shipping, weather, ports, customs, govt, banking, insurance, trade agreements, import/export restrictions.
- **3B** Buyer Intelligence + Supplier Intelligence.
- **3C** Market Intelligence + Country Intelligence (195 countries).
- **3D** Compliance Intelligence (country×product) — docs, licenses, inspection, testing, certificates, permits.
- **3E** **Packaging Intelligence (mandatory)** — country/product packaging checklist, primary/secondary/export packaging, palletization, container loading/type, wood treatment, fumigation, DG, hazard labels, UN markings, barcodes/QR, labelling rules, shelf life, temp/humidity, weight/stacking limits, packaging cost + time, Brain recommendations, downloadable checklist.
- **3F** Documentation Intelligence (country/product specific doc set).
- **3G** Trade News (Brain-summarized global/product/country impact — extends existing).
- **3H** PDF integration for Volume 3.

## VOLUME 4 — ENTERPRISE TRADE OS
- CRM (customers/suppliers/leads/partners), ERP-ready (inventory/warehouse/purchase/sales/mfg),
  Workflow Engine (tasks/approvals/assignments/notifications), Team Collaboration (comments/mentions/approvals/version history),
  Document Management (OCR/AI search/classification), Executive Dashboard (company+trade KPIs/revenue/profit/forecast),
  Enterprise APIs (ERP/SAP/Oracle/Microsoft/Tally/Zoho/QuickBooks), White Label (branding/reports/PDF/portal),
  Enterprise Security (RBAC/audit/logs/encryption/SSO).
- PDF integration for Volume 4.

## UNIVERSAL PDF ENGINE (cross-cutting)
Professional trade-intelligence report: cover page, branding, project summary, exec summary, full
Incoterm costing (EXW/FOB/FCA/FAS/CFR/CIF/CIP/DAP/DPU/DDP), landed cost, taxes/duties/FX/insurance/freight,
simulation, scenario comparison, risk, trade health, compliance, packaging checklist, documentation checklist,
buyer/supplier/country intelligence, trade news, Brain analysis, recommendations, next steps, charts/graphs,
appendix, disclaimers, Report ID, QR code, generation date, page numbers.

## Deliverables per volume
Updated blueprint · architecture diagrams · DB design · API contracts · Brain integration · PDF integration · test report · completion checklist.
