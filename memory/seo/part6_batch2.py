"""Part 6 batch 2 — hub pages: approved title/H1 + AnswerFirst + FAQ schema."""
import sys
ROOT = "/app/frontend/src/pages/"
IMP = 'import { AnswerFirst } from "@/components/AnswerFirst";\n'

def patch(f, reps, add_import=True):
    s = open(ROOT + f).read()
    for a, b in reps:
        if a not in s:
            sys.exit(f"MISSING in {f}: {a[:100]}")
        s = s.replace(a, b, 1)
    if add_import and IMP not in s:
        anchor = 'import SEO from "@/components/SEO";\n' if 'import SEO from "@/components/SEO";\n' in s else 'import SEO, '
        if anchor == 'import SEO, ':
            i = s.index(anchor); j = s.index("\n", i) + 1
            s = s[:j] + IMP + s[j:]
        else:
            s = s.replace(anchor, anchor + IMP, 1)
    open(ROOT + f, "w").write(s)
    print("ok", f)

# ── /buyers ──────────────────────────────────────────────────────────────────
patch("BuyerIntelligence.jsx", [
 ('title="Verified Buyer Intelligence · Find Global Importers with Evidence"\n        description="Discover verified global buyers by market, sector and HS code — each with an explainable trust score and cited source evidence. Powered by the Vametra AI Verified Buyer Intelligence Engine."\n        path="/buyers"',
  'title="Verified Importers List: 32 Countries, Evidence | Vametra AI"\n        description="Verified importers list: contact-verified, sanctions-screened buyers across 32 countries and 21 sectors, each with an explainable trust score and cited evidence. Search free by HS code and market."\n        path="/buyers"\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Verified Buyers", path: "/buyers" }]}\n        faqs={BUYERS_FAQ}'),
 ('          Buyers you can <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-violet-400">trust</span> — with the evidence to prove it.',
  '          Verified importers list <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-violet-400">with evidence</span>, not scraped leads.'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="buyers-answer"
        answer="A verified importers list is only useful if every record can be traced to evidence. Vametra AI ingests buyers from official, licence-cleared government sources, resolves a working contact, screens each company against sanctions lists and assigns an explainable trust score — {buyerRecords} records across {buyerCountries} countries and {buyerSectors} sectors. Search is free; contacts and evidence need a plan."
        rows={[
          { label: "Contact-verified buyer records", value: "{buyerRecords}" },
          { label: "Countries covered", value: "{buyerCountries}" },
          { label: "Sectors", value: "{buyerSectors}" },
          { label: "Trust bands", value: "Verified · Trusted · Emerging · Unverified" },
        ]}
        source="Official trade registries; Vametra AI Buyer Intelligence verification"
        links={[
          { to: "/tools/find-buyers", label: "Search buyers by HS code" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/export", label: "Export guides by market" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
          { to: "/services/buyer-discovery-service", label: "Done-for-you buyer discovery" },
        ]} />
      <PageFaq items={BUYERS_FAQ} heading="Verified importers — frequently asked questions" testIdPrefix="buyers-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>'''),
 ('export default function BuyerIntelligence() {',
  '''const BUYERS_FAQ = [
  { q: "What is a verified importers list?", a: "A list of importing companies whose trade activity is evidenced in official records and whose contact details have been confirmed. Vametra AI adds sanctions screening and an explainable trust score to every record, so you can see why a buyer is rated the way it is." },
  { q: "How many verified buyers does Vametra AI hold?", a: "{buyerRecords} contact-verified buyer records across {buyerCountries} countries and {buyerSectors} sectors, counted live from the platform. Coverage is stated per market; where a market has no verified records yet, the page says so." },
  { q: "What does the trust score mean?", a: "It summarises the evidence behind a record — source quality, contact resolution, recency and sanctions status — into Verified, Trusted, Emerging or Unverified bands. Every band is explained on the buyer profile." },
  { q: "Is the verified importers list free?", a: "Searching by HS code, market and sector is free, including company names, sectors and trust bands. Contact details, evidence trails, watchlists and exports require an account and an active plan." },
  { q: "Do you sell or show raw datasets?", a: "No. Vametra AI shows verified intelligence, never raw source dumps or scraped lead lists, and a buyer without a working contact is never published." },
];

export default function BuyerIntelligence() {'''),
])
s = open(ROOT + "BuyerIntelligence.jsx").read()
if 'from "@/components/PageFaq"' not in s:
    s = s.replace(IMP, IMP + 'import { PageFaq } from "@/components/PageFaq";\n', 1); open(ROOT + "BuyerIntelligence.jsx", "w").write(s)

# ── /brain ───────────────────────────────────────────────────────────────────
patch("Brain.jsx", [
 ('title="Vametra AI Brain · ChatGPT for Global Trade"\n        description="The Vametra AI Brain orchestrates 12 trade engines — compliance, tariffs, HSN, country intelligence, logistics and more — into one unified answer for global traders."\n        path="/brain"',
  'title="AI for Export Import Business: Vametra AI Brain"\n        description="AI for export import business: the Vametra AI Brain answers duty, HS code, FTA, landed cost and buyer questions by reading live WITS, OEC and registry data — not a generic chatbot. Free to try."\n        path="/brain"\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Vametra AI Brain", path: "/brain" }]}\n        faqs={BRAIN_FAQ}'),
 ('          The trade brain.<br /><span className="text-gradient">One mind for global trade.</span>',
  '          AI for export import business —<br /><span className="text-gradient">ask the Vametra AI Brain.</span>'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="brain-answer"
        answer="AI for an export import business has to answer with sourced numbers, not prose. The Vametra AI Brain routes each question to the right engine — tariffs from World Bank WITS for {tariffCountries} countries, demand from OEC/BACI, classification across {hsCodes} HS codes, {buyerRecords} verified buyers — and returns the figure, its source and the next step, in one reply."
        rows={[
          { label: "Engines orchestrated", value: "12" },
          { label: "Tariff countries", value: "{tariffCountries}" },
          { label: "HS codes", value: "{hsCodes}" },
          { label: "Verified buyers", value: "{buyerRecords}" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; OEC World (BACI); WCO HS-2022; official registries"
        links={[
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/buyers", label: "Verified importers list" },
          { to: "/export", label: "Export guides" },
          { to: "/countries/uae", label: "UAE trade profile" },
        ]} />
      <PageFaq items={BRAIN_FAQ} heading="AI for export import business — frequently asked questions" testIdPrefix="brain-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pb-16"><DownloadCTA /></section>'''),
 ('export default function BrainPage() {' if 'export default function BrainPage() {' in open(ROOT + "Brain.jsx").read() else 'export default function Brain() {',
  '''const BRAIN_FAQ = [
  { q: "How is the Vametra AI Brain different from ChatGPT for export import questions?", a: "It reads live trade data instead of recalling text. Duty comes from World Bank WITS, demand from OEC/BACI, classification from the WCO HS-2022 directory and buyers from verified registries, and every answer shows its source and data year." },
  { q: "What can I ask it?", a: "Import duty and FTA rate for a product and lane, the right HS code, landed cost, which markets import a product, export incentives, required documents and which verified buyers exist for an HS code and country." },
  { q: "Is the Vametra AI Brain free?", a: "Yes — you can ask questions and run the connected tools free. Saving work as a Trade Project and premium buyer contacts require an account and a plan." },
  { q: "Does it make numbers up when data is missing?", a: "No. Where a source has no record for a product-country pair, the Brain says so rather than estimating. An acknowledged gap is safer than an invented rate in a contract." },
];

''' + ('export default function BrainPage() {' if 'export default function BrainPage() {' in open(ROOT + "Brain.jsx").read() else 'export default function Brain() {')),
])
s = open(ROOT + "Brain.jsx").read()
if 'from "@/components/PageFaq"' not in s:
    s = s.replace(IMP, IMP + 'import { PageFaq } from "@/components/PageFaq";\n', 1); open(ROOT + "Brain.jsx", "w").write(s)

# ── /ai-assistant ────────────────────────────────────────────────────────────
patch("AiAssistant.jsx", [
 ('title="AI Trade Copilot · Ask Anything About Global Trade"\n        description="Vametra AI\'s AI Trade Copilot answers any export, HSN, FTA or certification question instantly. Free preview."\n        path="/ai-assistant"',
  'title="AI Trade Assistant for Duty, HS & Compliance | Vametra AI"\n        description="Free AI trade assistant: ask about import duty, HS codes, FTA rates, certifications and documents and get a sourced answer in seconds, powered by the Vametra AI Brain."\n        path="/ai-assistant"\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "AI Trade Assistant", path: "/ai-assistant" }]}'),
 ('      <PageHero testIdPrefix="ai" label="Vametra AI AI · Trade Copilot"\n        title="Ask anything. Export anywhere."',
  '      <PageHero testIdPrefix="ai" label="Vametra AI · Trade Copilot"\n        title="AI trade assistant for duty, HS codes and compliance."'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="ai-answer"
        answer="An AI trade assistant should answer a shipment question the way a customs broker would: with the rate, the code, the rule and the source. This copilot is a lightweight front door to the Vametra AI Brain — ask about duty, HS classification, FTA eligibility or documents and get a sourced reply; open the Brain for the full engine."
        rows={[
          { label: "Tariff countries", value: "{tariffCountries}" },
          { label: "HS codes", value: "{hsCodes}" },
          { label: "Cost", value: "Free preview" },
        ]}
        source="Vametra AI Brain over World Bank WITS, OEC/BACI and WCO HS-2022"
        links={[
          { to: "/brain", label: "Open the Vametra AI Brain" },
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/customs-compliance", label: "Customs compliance" },
          { to: "/countries/usa", label: "USA trade profile" },
        ]} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>'''),
])

# ── /intelligence ────────────────────────────────────────────────────────────
patch("Intelligence.jsx", [
 ('title="Trade Intelligence Hub · Gold, Silver, Oil, Currency Rates & Trends"\n        description="Live commodity prices, FX rates, and global market trends — curated for global traders, exporters and importers by Vametra AI."',
  'title="Trade Intelligence: Rates, Commodities & Trends | Vametra AI"\n        description="Trade intelligence hub for exporters and importers: gold, silver and oil prices, currency rates and global trade trends in one view, linked to duty, demand and buyer data for 56 countries."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Trade Intelligence", path: "/intelligence" }]}'),
 ('        title="The numbers that move the world."',
  '        title="Trade intelligence hub — gold, oil, currency and trade trends."'),
 ('        <DownloadCTA />',
  '''        <AnswerFirst testId="intel-answer" className="!px-0 !max-w-none !mt-0 mb-10"
          answer="Trade intelligence is the set of numbers that decide whether a shipment is still profitable when it lands: commodity prices that move your input cost, the currency pair you invoice in, and the tariff and demand data for the destination. This hub puts the market indicators on one screen and links each to the duty, demand and buyer tools for {tariffCountries} countries."
          rows={[
            { label: "Indicators", value: "Gold · silver · oil · FX" },
            { label: "Tariff countries", value: "{tariffCountries}" },
            { label: "Export guides", value: "{guides}" },
          ]}
          source="Market feeds as shown on screen; World Bank WITS; OEC World (BACI)"
          links={[
            { to: "/tools/product-research", label: "Import demand by HS code" },
            { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
            { to: "/trade-news", label: "Global trade news" },
            { to: "/export", label: "Export guides" },
            { to: "/regions/europe", label: "Europe export hub" },
          ]} />
        <DownloadCTA />'''),
])

# ── /expo ────────────────────────────────────────────────────────────────────
patch("Expo.jsx", [
 ('title="Global Trade Expos & Events · Live Calendar"\n        description="Every major trade expo, import/export fair, business and industry event worldwide — filtered by sector, country and date. List your own event to reach exporters and buyers."',
  'title="Trade Fairs and Exhibitions 2026: Live Calendar | Vametra AI"\n        description="Trade fairs and exhibitions calendar for exporters and importers: filter global expos by sector, country and date, see which lanes they serve, and list your own event."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Trade Fairs & Exhibitions", path: "/expo" }]}'),
 ('        title="Every trade event on earth — on one calendar."',
  '        title="Trade fairs and exhibitions — live global calendar."'),
 ('        <DownloadCTA />',
  '''        <AnswerFirst testId="expo-answer" className="!px-0 !max-w-none !mt-0 mb-10"
          answer="Trade fairs and exhibitions are still the fastest way to meet importers face to face, but only if the fair serves your lane. This calendar lists expos by sector, country and date and links each market to its export guides, so you can check the applied duty and real import demand before you book a stand — and list your own event to reach exporters."
          rows={[
            { label: "Filters", value: "Sector · country · date" },
            { label: "Linked export guides", value: "{guides}" },
            { label: "Tariff countries", value: "{tariffCountries}" },
          ]}
          source="Organiser listings as shown per event; World Bank WITS for linked duty data"
          links={[
            { to: "/expo/submit", label: "List your event" },
            { to: "/tools/find-buyers", label: "Find verified buyers" },
            { to: "/export", label: "Export guides" },
            { to: "/countries/uae", label: "UAE trade profile" },
            { to: "/regions/middle-east", label: "Middle East export hub" },
          ]} />
        <DownloadCTA />'''),
])

# ── /trade-news ──────────────────────────────────────────────────────────────
patch("TradeNews.jsx", [
 ('title="Global Trade News · Tariffs, Geopolitics, Currency, Shipping & Business"\n        description="Live global news for traders — tariffs, trade deals, currency, geopolitics, conflict, energy, shipping and business events. Filter by country and topic, updated daily."',
  'title="Global Trade News: Tariffs, Shipping, Policy | Vametra AI"\n        description="Global trade news for exporters and importers: tariffs, trade deals, currency, shipping and policy, filtered by country and topic and refreshed daily, with links to live duty and demand data."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Global Trade News", path: "/trade-news" }]}'),
 ('        title="The world\'s trade pulse — in real time."',
  '        title="Global trade news — tariffs, policy, currency and shipping."'),
 ('        <DownloadCTA />',
  '''        <AnswerFirst testId="news-answer" className="!px-0 !max-w-none !mt-0 mb-10"
          answer="Global trade news matters to an exporter when it changes a number: a tariff notification, a trade deal entering force, a currency move or a shipping disruption. This feed filters stories by country and topic, newest first, and links each market to its live applied duty and demand data so you can check the actual impact on your lane."
          rows={[
            { label: "Filters", value: "Country · topic" },
            { label: "Refresh", value: "Daily, newest first" },
            { label: "Linked tariff data", value: "{tariffCountries} countries" },
          ]}
          source="Headlines as attributed per story; World Bank WITS for linked duty data"
          links={[
            { to: "/tools/duty-calculator", label: "Check the duty now" },
            { to: "/intelligence", label: "Trade intelligence hub" },
            { to: "/export", label: "Export guides" },
            { to: "/corridors/india-to-usa", label: "India → USA corridor" },
            { to: "/countries/india", label: "India trade profile" },
          ]} />
        <DownloadCTA />'''),
])

# ── /customs-compliance ──────────────────────────────────────────────────────
patch("CustomsCompliance.jsx", [
 ('title="Vametra AI Trade Command Center™ — AI Global Trade Operating System"\n        description="The world\'s first AI-powered global trade operating system. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across 56 tariff-reporting countries, quote in your currency and any global currency, check duty, FTA benefits, incentives and routes — analysed by the Vametra AI Brain."\n        path="/customs-compliance"',
  'title="Customs Compliance for Exporters: AI Checks | Vametra AI"\n        description="Customs compliance for exporters in one engine: HS classification, applied and FTA duty for 56 countries, landed cost waterfall, incentives, documents and routes — analysed by the Vametra AI Brain."\n        path="/customs-compliance"\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Customs Compliance", path: "/customs-compliance" }]}\n        faqs={CC_FAQ}'),
 ('      <PageHero testIdPrefix="customs" label="Vametra AI Trade Command Center™"\n        title="The World\'s First AI-Powered Global Trade Operating System."',
  '      <PageHero testIdPrefix="customs" label="Vametra AI Trade Command Center™"\n        title="Customs compliance for exporters — clearance before cargo moves."'),
 ('      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>',
  '''      <AnswerFirst testId="customs-answer"
        answer="Customs compliance for exporters comes down to four checks before cargo moves: the right HS code, the duty and FTA rate the destination will actually apply, the documents and origin proof that unlock that rate, and a landed cost the buyer can clear. The Trade Command Center runs all four on live WITS data for {tariffCountries} countries and lets the Vametra AI Brain read the result back."
        rows={[
          { label: "Tariff countries", value: "{tariffCountries}" },
          { label: "HS codes", value: "{hsCodes}" },
          { label: "Waterfall", value: "EXW → FOB → CIF → landed" },
          { label: "Incentive rates", value: "Official schedules only (DGFT 4R)" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; WCO HS-2022; DGFT Appendix 4R"
        links={[
          { to: "/tools/hsn-finder", label: "HS code finder" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/academy/customs-clearance-playbook", label: "Customs clearance playbook" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
        ]} />
      <PageFaq items={CC_FAQ} heading="Customs compliance — frequently asked questions" testIdPrefix="customs-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>'''),
 ('export default function CustomsCompliance() {',
  '''const CC_FAQ = [
  { q: "What does customs compliance for exporters involve?", a: "Correct HS classification, the applied or preferential duty the destination charges, the documents and rules-of-origin proof required to claim an FTA rate, destination VAT/GST and any restricted-goods or labelling rules. Getting the code wrong invalidates everything downstream." },
  { q: "Where does the duty data come from?", a: "Applied MFN and preferential tariffs are read live from World Bank WITS / UNCTAD TRAINS at HS6 level for {tariffCountries} reporting countries, with the data year shown on every rate." },
  { q: "Can I claim an FTA rate automatically?", a: "No. A preferential rate is conditional on meeting rules of origin and presenting valid origin documentation at clearance. The engine shows the rate; you still have to qualify for it, so price the applied rate unless you can evidence the preferential one." },
  { q: "Does the engine cover imports as well as exports?", a: "Yes. Origin and destination are both yours to set, so the same checks work for an import into your own market or a third-country lane." },
];

export default function CustomsCompliance() {'''),
])
s = open(ROOT + "CustomsCompliance.jsx").read()
if 'from "@/components/PageFaq"' not in s:
    s = s.replace(IMP, IMP + 'import { PageFaq } from "@/components/PageFaq";\n', 1); open(ROOT + "CustomsCompliance.jsx", "w").write(s)

# ── /academy ─────────────────────────────────────────────────────────────────
patch("Academy.jsx", [
 ('title="Trade Learning Academy · Free Import, Export & Customs Courses"\n        description="Master international trade in 6 weeks. Free, structured lessons on import process, export process, documentation, customs clearance, FTA arbitrage and more."',
  'title="Learn Export Import Business: Free Courses | Vametra AI"\n        description="Learn export import business with 9 free structured courses: trade basics, import and export process, documentation, customs clearance, Incoterms 2020, FTA arbitrage, trade finance and compliance."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Academy", path: "/academy" }]}'),
 ('        title="Master global trade. In weeks, not years."',
  '        title="Learn export import business — free courses from first shipment to FTA."'),
 ('        <DownloadCTA id="download" />',
  '''        <AnswerFirst testId="academy-answer" className="!px-0 !max-w-none !mt-0 mb-10"
          answer="To learn the export import business you need the sequence, not a glossary: how a trade is structured, how goods are classified and cleared, which documents move with them, what Incoterms shift the risk, and how FTAs change the price. These nine free courses follow that order and link each lesson to the live tool that applies it."
          rows={[
            { label: "Courses", value: "9 · 100% free" },
            { label: "Levels", value: "Beginner → Advanced" },
            { label: "Applied in", value: "Duty, HS and landed-cost tools" },
          ]}
          source="Vametra AI Academy curriculum"
          links={[
            { to: "/academy/export-process-101", label: "Export process 101" },
            { to: "/academy/incoterms-2020", label: "Incoterms 2020" },
            { to: "/tools/export-readiness", label: "Export readiness assessment" },
            { to: "/tools/hsn-finder", label: "HS code finder" },
            { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
          ]} />
        <DownloadCTA id="download" />'''),
])

# ── /pricing ─────────────────────────────────────────────────────────────────
patch("Pricing.jsx", [
 ('title="Pricing · Vametra AI Trade Intelligence Plans"\n        description="Simple, transparent pricing for Vametra AI. Your first trade report is free. Go unlimited with Monthly or Annual Pro plans — customs duties, HS codes, landed cost, expos and trade news. Cancel anytime."',
  'title="Export Import Software Pricing & Plans | Vametra AI"\n        description="Export import software pricing: the trade tools are free, your first trade report is free, and Pro plans unlock unlimited reports and verified buyer contacts. Monthly or annual, cancel anytime."'),
 ('<h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl mt-3">Unlock the world\'s trade desk</h1>',
  '<h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl mt-3">Export import software pricing — start free, upgrade when it pays</h1>'),
])

# ── /blog list ───────────────────────────────────────────────────────────────
patch("Blog.jsx", [
 ('title="Vametra AI Blog · Export, Import, Compliance & Trade News"\n        description="Long-form guides for global traders — export, import, compliance, logistics and trade intelligence. Updated weekly."',
  'title="Export Import Blog: Guides, RoDTEP, Incoterms | Vametra AI"\n        description="Export import blog for Indian traders: IEC code, RoDTEP, Incoterms 2020, India-UAE CEPA product list, payment terms and how to find buyers in the GCC — practical, dated guides."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Blog", path: "/blog" }]}'),
 ('      <PageHero testIdPrefix="blog" label="Knowledge Center"\n        title="Stories, guides & playbooks for traders."',
  '      <PageHero testIdPrefix="blog" label="Knowledge Center"\n        title="Export import blog — practical guides for Indian traders."'),
])

# ── /countries index ─────────────────────────────────────────────────────────
patch("CountriesIndex.jsx", [
 ('title="Country Trade Profiles · Imports, Exports, Customs & Opportunities"\n        description="Country-by-country trade profiles — imports, exports, customs duties, trade agreements, compliance and live news for India, UAE, USA, Australia, Armenia and 250+ markets."',
  'title="Country Trade Profiles: Tariffs, Imports, Buyers | Vametra"\n        description="Country trade profiles for India, UAE, USA, Australia and Armenia: imports and exports, applied customs duties, trade agreements, compliance and verified buyer coverage, linked to per-product export guides."'),
 ('        title="Pick a market. See the playbook."',
  '        title="Country trade profiles — tariffs, imports and verified buyers."'),
 ('      <AnswerBlock testId="countries-answer" label="How to use these profiles"',
  '''      <AnswerFirst testId="countries-answer-first"
        answer="A country trade profile answers what a market imports, what duty it applies, which agreements lower that duty and whether verified buyers exist there. Vametra AI publishes written profiles for five markets and backs every one with live tariff data for {tariffCountries} reporting countries and verified buyer records across {buyerCountries} countries, linked to per-product export guides."
        rows={[
          { label: "Written country profiles", value: "5" },
          { label: "Tariff-reporting countries", value: "{tariffCountries}" },
          { label: "Countries with verified buyers", value: "{buyerCountries}" },
          { label: "Export guides", value: "{guides}" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; OEC World (BACI); official registries"
        links={[
          { to: "/countries/uae", label: "UAE trade profile" },
          { to: "/countries/usa", label: "USA trade profile" },
          { to: "/regions", label: "Export regions" },
          { to: "/tools/duty-calculator", label: "Custom duty calculator" },
          { to: "/corridors", label: "India trade corridors" },
        ]} />
      <AnswerBlock testId="countries-answer" label="How to use these profiles"'''),
])

# ── /suppliers + /directory → thin seeded sample data: noindex, no app claim ─
patch("Suppliers.jsx", [
 ('title="Supplier Discovery · Verified Indian Manufacturers & Exporters"\n        description="Discover verified Indian suppliers and manufacturers — by product, category and country. Free preview, full directory in the app."',
  'title="Indian Manufacturers and Exporters Directory | Vametra AI"\n        description="Indian manufacturers and exporters directory — sample listings while verified supplier coverage is built. Use verified buyer intelligence and export guides for live data today."\n        noindex'),
 ('        title="Verified suppliers. Verified opportunities."',
  '        title="Indian manufacturers and exporters directory — coverage in progress."'),
], add_import=False)
patch("Directory.jsx", [
 ('title="Vametra AI Directories · Exporters, Importers, Suppliers, CHA & Agents"\n        description="Verified directories of Indian exporters, global importers, suppliers, customs house agents and export agents — by Vametra AI."',
  'title="Exporters Importers Directory: CHA, Agents | Vametra AI"\n        description="Exporters importers directory — sample listings of exporters, importers, suppliers and customs house agents while verified coverage is built. For live verified buyers use Buyer Intelligence."\n        noindex'),
 ('        title="Verified directories. Verified opportunities."',
  '        title="Exporters importers directory — CHA, agents and suppliers."'),
 ('      <SEO title={`${label} Directory · Verified by Vametra AI`}\n        description={`Verified ${label.toLowerCase()} directory — searchable by name, country and category. Powered by Vametra AI.`}',
  '      <SEO title={`${label} Directory · Vametra AI`} noindex\n        description={`${label} directory — sample listings searchable by name, country and category while verified coverage is built.`}'),
], add_import=False)

# ── /services list ───────────────────────────────────────────────────────────
patch("Services.jsx", [
 ('title="Business Services · RCMC, GST, IEC, Export Consulting"\n        description="Vametra AI Business Services — RCMC, GST, IEC and company registration handled by certified CAs. Plus export, import, compliance, market-entry and sourcing consulting."',
  'title="Export Import Services India: IEC, RCMC, GST | Vametra AI"\n        description="Export import services in India: IEC code, RCMC and GST registration handled by certified CAs, plus export, import, compliance, market-entry, sourcing and buyer-discovery consulting."\n        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Services", path: "/services" }]}'),
 ('        title="Compliance, registrations, consulting. Done."',
  '        title="Export import services India — registration to market entry."'),
])

# ── /corridors, /products, /industries indexes ───────────────────────────────
patch("Corridors.jsx", [
 ('title="Trade Corridors · India to UAE, USA, Australia, Armenia"',
  'title="India Trade Corridors: Duty, FTA, Shipping | Vametra AI"'),
 ('        title="From your factory to their dock."',
  '        title="India trade corridors — duty, FTA and shipping by destination."'),
], add_import=False)
patch("Products.jsx", [
 ('title="Product Trade Profiles · Basmati, Spices, Pharma & More"',
  'title="Export Products from India: HS Code, Duty, Buyers | Vametra"'),
 ('        title="Pick a product. See the global playbook."',
  '        title="Export products from India — HS code, duty and buyers per product."'),
], add_import=False)
patch("Industries.jsx", [
 ('title="Industry Trade Profiles · 8 sectors, 100+ markets"',
  'title="Export Industries India: 8 Sector Trade Profiles | Vametra"'),
 ('        title="Pick your sector. See your edge."',
  '        title="Export industries India — sector profiles with real trade data."'),
], add_import=False)

# ── Home ─────────────────────────────────────────────────────────────────────
patch("Home.jsx", [
 ('        title="Vametra AI · AI-Powered Global Trade Intelligence Platform"',
  '        title="Trade Intelligence Platform for Exporters | Vametra AI"'),
 ('                Rule global trade.<br />\n                <span className="gradient-text">Before cargo moves.</span>',
  '                The AI trade intelligence platform<br />\n                <span className="gradient-text">for exporters and importers.</span>'),
], add_import=False)
