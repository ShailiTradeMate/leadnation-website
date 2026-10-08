import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { CommandCenterTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, Lightning } from "@phosphor-icons/react";

export default function LandedCostCalculator() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "", from: p.get("from") || "", to: p.get("to") || "" };
  return (
    <>
      <SEO title="Landed Cost Calculator · FOB → CIF → Landed with Real Duty, VAT & FX"
        description="Build your full export cost waterfall — Ex-Works, FOB, CIF and landed cost at destination with live WITS duty, VAT/GST and exchange rates. Compare what your buyer pays across markets and quote in two currencies."
        path="/tools/landed-cost-calculator"
        keywords="landed cost calculator, FOB CIF calculator, export costing, import cost calculator, DDP price calculator, buyer landed cost comparison"
        schema={{ "@context": "https://schema.org", "@type": "WebApplication", name: "Vametra AI Landed Cost Calculator", applicationCategory: "BusinessApplication", operatingSystem: "Web", offers: { "@type": "Offer", price: "0", priceCurrency: "USD" } }}
      />
      <ToolShell testIdPrefix="lcc" label="Landed Cost Calculator"
        title="Your true landed cost — with real duty, VAT and FX."
        sub="Enter your per-unit costs once. The Trade Command Center engine applies the destination's live tariff and VAT, converts to your buyer's currency, ranks the markets where your buyer pays the least, and the Vametra AI Brain reads the numbers back to you.">
        <div className="space-y-5">
          <CommandCenterTool initial={initial} showIntro={false} />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=compile" data-testid="lcc-open-engine" className="btn-ghost"><Lightning size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <Link to="/command-center" data-testid="lcc-open-workspace" className="btn-ghost">Save as a Trade Project (workspace)</Link>
          </div>
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
