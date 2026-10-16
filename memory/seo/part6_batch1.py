"""Part 6 batch 1 — tools pages: title/H1 per approved plan + AnswerFirst block."""
import re, sys
ROOT = "/app/frontend/src/pages/"
IMP = 'import { AnswerFirst } from "@/components/AnswerFirst";\n'

def patch(f, reps, add_import=True):
    s = open(ROOT + f).read()
    for a, b in reps:
        if a not in s:
            sys.exit(f"MISSING in {f}: {a[:90]}")
        s = s.replace(a, b, 1)
    if add_import and IMP not in s:
        s = s.replace('import SEO from "@/components/SEO";\n', 'import SEO from "@/components/SEO";\n' + IMP, 1)
    open(ROOT + f, "w").write(s)
    print("ok", f)

# ── /tools/duty-calculator ───────────────────────────────────────────────────
patch("DutyCalculator.jsx", [
 ('title="Customs Duty Calculator · Real Import Tariffs for Any Trade Lane"\n        description="Check the real import duty for any product into 56 countries — MFN and preferential rates from World Bank WITS / UNCTAD TRAINS, destination tax breakdown, and the official export-support schemes of your own exporting country. Free, by HS code."',
  'title="Custom Duty Calculator India & 56 Countries | Vametra AI"\n        description="Free custom duty calculator for India and 56 reporting countries: applied MFN and FTA rates by HS code from World Bank WITS / UNCTAD TRAINS, destination VAT and official export schemes."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Custom Duty Calculator", path: "/tools/duty-calculator" }]}\n        faqs={FAQ.map(([q, a]) => ({ q, a }))}'),
 ('title="Real import duty, by HS code, for 56 countries."',
  'title="Custom duty calculator India — real applied tariffs by HS code."'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="duty-answer"
        answer="A custom duty calculator tells you the import tariff a destination applies to your product's HS code. Vametra AI reads the applied MFN rate and any preferential (FTA) rate for your origin from World Bank WITS / UNCTAD TRAINS for {tariffCountries} reporting countries, then adds destination VAT/GST — so the number you quote is the number your buyer pays."
        rows={[
          { label: "Tariff-reporting countries", value: "{tariffCountries}" },
          { label: "HS codes searchable", value: "{hsCodes}" },
          { label: "Tariff level", value: "HS6 · applied + preferential" },
          { label: "Export-support schemes", value: "Official authority pages only" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; DGFT Appendix 4R for India RoDTEP"
        links={[
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/export", label: "Export guides by product and market" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
          { to: "/customs-compliance", label: "Customs compliance" },
        ]} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>'''),
])

# ── /tools/hsn-finder ────────────────────────────────────────────────────────
patch("tools/HsnFinder.jsx", [
 ('title="HS Code Finder · All 5,606 HS Codes with Import Duty for Any Trade Lane"\n        description="Find the correct HS / HSN code for any product from the complete WCO HS-2022 nomenclature. Pick your exporting and importing country to see the live MFN and preferential import duty, destination VAT and origin-specific export benefits. Free, instant, global."',
  'title="HS Code Finder: 5,606 Codes with Import Duty | Vametra AI"\n        description="Free HS code finder covering all 5,606 WCO HS-2022 codes. Search by product name, then see live import duty, FTA rate and destination VAT for any of 56 countries."'),
 ('title="Find your HS code — then see what it costs on your trade lane."',
  'title="HS code finder with import duty for any trade lane."'),
 ('      <AnswerBlock testId="hsn-answer" label="Classification in practice"',
  '''      <AnswerFirst testId="hsn-answer-first"
        answer="An HS code finder matches your product description to the six-digit Harmonized System code customs uses worldwide. Vametra AI searches all {hsCodes} WCO HS-2022 lines, then shows the live import duty, preferential rate and destination VAT for your exact origin-destination lane — so classification and cost are checked in one step."
        rows={[
          { label: "HS codes indexed", value: "{hsCodes}" },
          { label: "Nomenclature", value: "WCO HS-2022 · 6-digit" },
          { label: "Duty lanes", value: "{tariffCountries} reporting countries" },
          { label: "Search", value: "Product name or code prefix" },
        ]}
        source="WCO HS-2022 nomenclature; World Bank WITS / UNCTAD TRAINS tariffs"
        links={[
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/product-research", label: "Import demand by HS code" },
          { to: "/export", label: "Export guides" },
          { to: "/countries/india", label: "India trade profile" },
          { to: "/academy/trade-documentation", label: "Trade documentation course" },
        ]} />
      <AnswerBlock testId="hsn-answer" label="Classification in practice"'''),
])

# ── /tools/landed-cost-calculator ────────────────────────────────────────────
patch("tools/LandedCostCalculator.jsx", [
 ('title="Landed Cost Calculator · FOB → CIF → Landed with Real Duty, VAT & FX"\n        description="Build your full export cost waterfall — Ex-Works, FOB, CIF and landed cost at destination with live WITS duty, VAT/GST and exchange rates. Compare what your buyer pays across markets and quote in two currencies."',
  'title="Landed Cost Calculator: FOB to Landed Price | Vametra AI"\n        description="Free landed cost calculator: Ex-Works → FOB → CIF → landed at destination with live WITS duty, VAT/GST and FX for 56 countries. Compare buyer landed cost across markets, quote in two currencies."'),
 ('title="Your true landed cost — with real duty, VAT and FX."',
  'title="Landed cost calculator — FOB → CIF → landed with real duty."'),
 ('      <AnswerBlock testId="lcc-answer" label="Method"',
  '''      <AnswerFirst testId="lcc-answer-first"
        answer="A landed cost calculator adds freight, insurance, import duty, destination VAT/GST and clearance to your factory price to show what the buyer actually pays. Vametra AI applies the live applied or preferential tariff for your HS code and lane from World Bank WITS across {tariffCountries} countries, converts to the buyer's currency and ranks the cheapest markets."
        rows={[
          { label: "Incoterm waterfall", value: "EXW → FOB → CIF → landed" },
          { label: "Duty source", value: "WITS / TRAINS · HS6" },
          { label: "Destination markets", value: "{tariffCountries}" },
          { label: "Currencies", value: "Yours + buyer's" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; destination VAT/GST schedules"
        links={[
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/product-research", label: "Which markets import most" },
          { to: "/academy/incoterms-2020", label: "Incoterms 2020 course" },
          { to: "/corridors/india-to-usa", label: "India → USA corridor" },
          { to: "/export/basmati-rice", label: "Basmati rice export guides" },
        ]} />
      <AnswerBlock testId="lcc-answer" label="Method"'''),
])

# ── /tools/export-incentive-finder ───────────────────────────────────────────
patch("tools/ExportIncentiveFinder.jsx", [
 ('title="Export Incentive Finder · Official Export-Support Schemes by Country"\n        description="Find the official export-support schemes your own country publishes — remissions, duty drawback, export VAT refunds, duty-free input regimes, export credit and grants — plus the import duty your buyer pays at destination. 50+ exporting countries, every scheme linked to its authority."',
  'title="Export Incentive Calculator India: RoDTEP, EPCG | Vametra AI"\n        description="Export incentive calculator for India: published RoDTEP rate by HS code from DGFT Appendix 4R, plus duty drawback, EPCG and other official schemes — and the import duty your buyer pays at destination."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Export Incentive Calculator", path: "/tools/export-incentive-finder" }]}'),
 ('title="What your country gives you — and what your buyer pays."',
  'title="Export incentive calculator India — RoDTEP, drawback, EPCG."'),
 ('          <CountryIncentiveMap />\n',
  '''          <CountryIncentiveMap />
          <AnswerFirst testId="inc-answer" className="!px-0 !mt-2 !max-w-none"
            answer="An export incentive calculator for India returns the remission an exporter can claim on a shipment. Vametra AI reads the published RoDTEP rate for your HS code straight from DGFT Appendix 4R and lists the other official schemes — duty drawback, EPCG, Advance Authorisation — each linked to its administering authority. No rate is shown unless a government publishes it."
            rows={[
              { label: "India rate schedule", value: "RoDTEP · DGFT Appendix 4R" },
              { label: "Other schemes", value: "Drawback · EPCG · AA · interest equalisation" },
              { label: "Other exporting countries", value: "Schemes named, authority linked" },
              { label: "Destination duty", value: "{tariffCountries} countries via WITS" },
            ]}
            source="DGFT Appendix 4R; national export-support authorities; World Bank WITS"
            links={[
              { to: "/tools/duty-calculator", label: "Custom duty calculator" },
              { to: "/blog/rodtep-explained-2026", label: "RoDTEP explained" },
              { to: "/services/rcmc-registration", label: "RCMC registration" },
              { to: "/export", label: "Export guides" },
              { to: "/countries/india", label: "India trade profile" },
            ]} />
'''),
])

# ── /tools/find-buyers ───────────────────────────────────────────────────────
patch("tools/FindBuyers.jsx", [
 ('title="Buyer Discovery · Verified Importers by HS Code & Country"\n        description="Search 27,000+ verified importer records by HS code and market. See trust scores, sectors and HS families for free; unlock contacts, evidence and watchlists in Buyer Intelligence."\n        path="/tools/find-buyers"',
  'title="How to Find Buyers for Export from India | Vametra AI"\n        description="How to find buyers for export from India: search contact-verified importer records by HS code across 32 countries, with trust scores and sanctions screening. Free search; contacts with a plan."\n        path="/tools/find-buyers"\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Find Buyers", path: "/tools/find-buyers" }]}\n        faqs={FB_FAQ}'),
 ('title="Who imports your product — by HS code, by country."',
  'title="How to find buyers for export from India — verified importers."'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="fb-answer"
        answer="To find buyers for export from India, start from your HS code, not a directory: pick the code and the market, and Vametra AI returns importers whose trade in that code is evidenced in official registries. Every record is contact-verified and sanctions-screened — {buyerRecords} buyers across {buyerCountries} countries and {buyerSectors} sectors — and markets without coverage say so instead of showing invented leads."
        rows={[
          { label: "Contact-verified buyer records", value: "{buyerRecords}" },
          { label: "Countries with buyer coverage", value: "{buyerCountries}" },
          { label: "Sectors", value: "{buyerSectors}" },
          { label: "Screening", value: "Sanctions + contact resolution" },
        ]}
        source="Official trade registries, verified by Vametra AI Buyer Intelligence"
        links={[
          { to: "/buyers", label: "Verified importers list" },
          { to: "/tools/product-research", label: "Which markets import your product" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
          { to: "/blog/how-to-find-buyers-in-gcc", label: "How to find buyers in the GCC" },
        ]} />
      <PageFaq items={FB_FAQ} testIdPrefix="fb-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>'''),
 ('export default function FindBuyers() {',
  '''const FB_FAQ = [
  { q: "How do I find buyers for export from India?", a: "Classify your product to its HS code, pick the destination market, and search importers evidenced in official trade registries for that code. Vametra AI returns contact-verified, sanctions-screened records with a trust score; free search shows company, sector and HS family, and a plan unlocks contacts and evidence." },
  { q: "Are these real importers or scraped leads?", a: "Real importers. Records are ingested from official, licence-cleared government sources, then verified for contact and screened against sanctions lists before publication. A buyer without a working contact is never shown." },
  { q: "Which countries have verified buyer coverage?", a: "Contact-verified buyer records currently cover {buyerCountries} countries and {buyerSectors} sectors. Where a market is not yet covered, the tool shows real import demand data and says coverage is expanding rather than inventing buyers." },
  { q: "Is buyer search free?", a: "Searching and seeing company names, sectors, HS families and trust scores is free with no signup. Contact details, evidence trails and watchlists require an account and an active plan." },
];

export default function FindBuyers() {'''),
])
s = open(ROOT + "tools/FindBuyers.jsx").read()
if "PageFaq" not in s.split("export default")[0]:
    s = s.replace(IMP, IMP + 'import { PageFaq } from "@/components/PageFaq";\n', 1)
    open(ROOT + "tools/FindBuyers.jsx", "w").write(s)

# ── /tools/product-research ──────────────────────────────────────────────────
patch("tools/ProductResearch.jsx", [
 ('title="Product Research · Real World Import Demand by HS Code (OEC / BACI)"\n        description="See who imports your product and how much — top importing and exporting countries, total world trade value and multi-year trend for any of 5,606 HS codes. Real OEC World / CEPII BACI data, not estimates."',
  'title="Export Product Research: Real Import Demand | Vametra AI"\n        description="Free export product research tool: top importing countries, world trade value and multi-year trend for any of 5,606 HS codes, from OEC World / CEPII BACI customs data — measured flows, not estimates."'),
 ('title="Which countries actually buy your product?"',
  'title="Export product research with real import demand by HS code."'),
 ('      <AnswerBlock testId="pr-answer" label="Reading the output"',
  '''      <AnswerFirst testId="pr-answer-first"
        answer="Export product research means checking that a market measurably imports your product before you spend on it. Vametra AI shows, for any of {hsCodes} HS codes, the latest published world trade value, the ranked importing and exporting countries with share, and the multi-year trend — from OEC World / CEPII BACI, built from national customs declarations."
        rows={[
          { label: "HS codes researchable", value: "{hsCodes}" },
          { label: "Data type", value: "Measured bilateral flows" },
          { label: "Granularity", value: "HS6 · latest published year + trend" },
          { label: "Published export guides", value: "{guides}" },
        ]}
        source="OEC World (CEPII BACI / UN Comtrade)"
        links={[
          { to: "/tools/duty-calculator", label: "Check duty for the top markets" },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/export", label: "Export guides by product" },
          { to: "/regions/middle-east", label: "Middle East export hub" },
          { to: "/tools/find-buyers", label: "Find verified buyers" },
        ]} />
      <AnswerBlock testId="pr-answer" label="Reading the output"'''),
])

# ── /tools/export-readiness ──────────────────────────────────────────────────
patch("tools/ExportReadiness.jsx", [
 ('title="Export Readiness Score · Free 60-second Assessment"\n        description="Score your export readiness in 60 seconds. Get a personalised, actionable roadmap to your first international shipment — registrations, certifications, packaging and market pricing, in priority order. Free."',
  'title="Export Readiness Assessment: Free 60-Sec Score | Vametra AI"\n        description="Free export readiness assessment: answer six questions, get a score and a prioritised roadmap to your first shipment — IEC, RCMC, GST/LUT, certifications, packaging and market pricing."'),
 ('title="Are you ready to export? Find out in 60 seconds."',
  'title="Export readiness assessment — your score in 60 seconds."'),
 ('      <AnswerBlock testId="er-answer" label="What readiness actually means"',
  '''      <AnswerFirst testId="er-answer-first"
        answer="An export readiness assessment checks whether a business has the registrations, product compliance, packaging and pricing in place to ship abroad. Vametra AI's six-question version scores you in about 60 seconds and returns the steps in the order they unblock each other — IEC and RCMC before incentives, classification before duty, landed cost before a quote."
        rows={[
          { label: "Questions", value: "6" },
          { label: "Time", value: "≈ 60 seconds" },
          { label: "Output", value: "Score + prioritised roadmap" },
          { label: "Cost", value: "Free · no signup" },
        ]}
        source="Vametra AI readiness model; DGFT registration requirements"
        links={[
          { to: "/services/iec-registration", label: "IEC code registration" },
          { to: "/services/rcmc-registration", label: "RCMC certificate" },
          { to: "/tools/hsn-finder", label: "Find your HS code" },
          { to: "/academy/export-process-101", label: "Export process 101 course" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
        ]} />
      <AnswerBlock testId="er-answer" label="What readiness actually means"'''),
])

# ── /tools hub ───────────────────────────────────────────────────────────────
patch("ToolsHub.jsx", [
 ('title="Free Trade Tools · HSN Finder, Duty Calculator, Buyer Discovery"\n        description="Vametra AI\'s free trade toolbox — HSN finder, customs duty calculator, landed cost calculator, export incentive finder, buyer discovery, export readiness score, AI trade copilot. Real WITS, OEC and official-authority data, no signup."',
  'title="Free Export Import Tools: HS, Duty, Landed Cost | Vametra AI"\n        description="Eight free export import tools: HS code finder, custom duty calculator, landed cost calculator, export incentive finder, product research, buyer discovery, readiness score and AI copilot. Real WITS and OEC data, no signup."'),
 ('title="Eight tools. One engine. Real data on every screen."',
  'title="Free export import tools for every shipment decision."'),
 ('      <AnswerBlock testId="tools-answer" label="How these fit together"',
  '''      <AnswerFirst testId="tools-answer-first"
        answer="These free export import tools run in sequence on one engine: find the HS code, check the import duty for your lane, build landed cost, confirm the market really imports the product, then find contact-verified buyers. Every figure comes from World Bank WITS, OEC/BACI or an official authority — {hsCodes} HS codes, {tariffCountries} tariff countries, {buyerCountries} buyer countries — with no signup."
        rows={[
          { label: "Tools", value: "8 · all free" },
          { label: "HS codes", value: "{hsCodes}" },
          { label: "Tariff-reporting countries", value: "{tariffCountries}" },
          { label: "Verified buyer records", value: "{buyerRecords}" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; OEC World (BACI); WCO HS-2022; DGFT"
        links={[
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/export", label: "Export guides" },
          { to: "/countries", label: "Country trade profiles" },
        ]} />
      <AnswerBlock testId="tools-answer" label="How these fit together"'''),
])
