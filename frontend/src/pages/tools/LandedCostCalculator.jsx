import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { CommandCenterTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, Lightning } from "@phosphor-icons/react";

const FAQ = [
  {
    q: "What is landed cost and why does it decide the deal?",
    a: "Landed cost is what your buyer actually pays to have the goods available at their premises — your price, plus freight and insurance to the agreed Incoterm, plus the destination's import duty, plus its VAT or GST on the duty-inclusive value, plus clearance charges. Buyers compare landed cost, not FOB, which is why two exporters with the same factory price can be far apart commercially.",
  },
  {
    q: "Which Incoterms does the calculator handle?",
    a: "The full waterfall from Ex-Works through FOB and CIF to landed at destination, so you can see exactly where your responsibility ends and your buyer's begins under each term. Quoting DDP without having built this waterfall is the most common way exporters lose their margin after the contract is signed.",
  },
  {
    q: "Where do the duty, tax and exchange rates come from?",
    a: "Applied and preferential tariffs are read live from World Bank WITS / UNCTAD TRAINS at HS6 level and cached for seven days, with the source data year shown. Destination VAT or GST on imports and the FX conversion are applied by the same Trade Command Center engine the platform uses — there is no separate simplified dataset for this tool.",
  },
  {
    q: "Can I compare several destination markets at once?",
    a: "Yes. Enter your per-unit costs once and the engine ranks the markets where your buyer pays the least landed, which is often a very different ordering from the markets that import the most. That gap between demand ranking and landed-cost ranking is usually where the opportunity is.",
  },
  {
    q: "Can I quote in my buyer's currency?",
    a: "Yes — results convert to the destination currency alongside your own, so you can send a figure your buyer can act on without a second spreadsheet. Save the scenario as a Trade Project in the Command Center if you want to revisit it when rates or freight move.",
  },
  {
    q: "Does it work for imports and for non-India origins?",
    a: "Yes. Origin and destination are both yours to set across the supported reporting countries, so the same waterfall works for an import into your own market or for a third-country lane. Only the export-incentive layer is origin-restricted, because it exists only where a government publishes an official rate schedule.",
  },
];

export default function LandedCostCalculator() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "", from: p.get("from") || "", to: p.get("to") || "" };
  return (
    <>
      <SEO title="Landed Cost Calculator · FOB → CIF → Landed with Real Duty, VAT & FX"
        description="Build your full export cost waterfall — Ex-Works, FOB, CIF and landed cost at destination with live WITS duty, VAT/GST and exchange rates. Compare what your buyer pays across markets and quote in two currencies."
        path="/tools/landed-cost-calculator"
        keywords="landed cost calculator, FOB CIF calculator, export costing, import cost calculator, DDP price calculator, buyer landed cost comparison"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Landed Cost Calculator", path: "/tools/landed-cost-calculator" }]}
        faqs={FAQ}
        schema={{ "@context": "https://schema.org", "@type": "WebApplication", name: "Vametra AI Landed Cost Calculator", applicationCategory: "BusinessApplication", operatingSystem: "Web", offers: { "@type": "Offer", price: "0", priceCurrency: "USD" } }}
      />
      <ToolShell testIdPrefix="lcc" label="Landed Cost Calculator"
        title="Your true landed cost — with real duty, VAT and FX."
        sub="Enter your per-unit costs once and set your own export and import countries. The Trade Command Center engine applies the destination's live tariff and VAT, converts to your buyer's currency, ranks the markets where your buyer pays the least, and the Vametra AI Brain reads the numbers back to you.">
        <div className="space-y-5">
          <CommandCenterTool initial={initial} showIntro={false} />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=compile" data-testid="lcc-open-engine" className="btn-ghost"><Lightning size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <Link to="/command-center" data-testid="lcc-open-workspace" className="btn-ghost">Save as a Trade Project (workspace)</Link>
          </div>
        </div>
      </ToolShell>
      <AnswerBlock testId="lcc-answer" label="Method"
        title="Where exporters lose money in the waterfall">
        <p>
          Almost always in the same two places. The first is the destination's indirect tax: VAT or
          GST on imports is levied on the customs value plus duty, so it amplifies the tariff rather
          than sitting beside it. Omitting it from a DDP quote understates your cost by more than
          most people's entire margin.
        </p>
        <p>
          The second is assuming a preferential rate you have not qualified for. A trade agreement
          publishes a lower rate, but access to it is conditional on meeting rules of origin and
          presenting valid origin documentation at clearance. Price the applied rate unless you can
          evidence the preferential one — then treat the saving as upside, not as your base case.
        </p>
        <p>
          Build the waterfall before you quote, not after the buyer pushes back. Enter your costs
          once, let the engine apply live duty, destination tax and FX across every candidate
          market, and you will usually find the cheapest market for your buyer is not the one you
          were planning to approach.
        </p>
      </AnswerBlock>
      <PageFaq items={FAQ} testIdPrefix="lcc-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
