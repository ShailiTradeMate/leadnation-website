import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { TradeStatsTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, ChartLineUp } from "@phosphor-icons/react";

export default function ProductResearch() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "" };
  return (
    <>
      <SEO title="Product Research · Real World Import Demand by HS Code (OEC / BACI)"
        description="See who imports your product and how much — top importing and exporting countries, total world trade value and multi-year trend for any of 5,606 HS codes. Real OEC World / CEPII BACI data, not estimates."
        path="/tools/product-research"
        keywords="export product research, top importing countries by product, world import demand by HS code, trade statistics by product, best export markets"
      />
      <ToolShell testIdPrefix="pr" label="Product Research"
        title="Which countries actually buy your product?"
        sub="Pick any product or HS code. We show the latest-year world trade value, the top importing and exporting countries with their share, and the multi-year trend — straight from OEC World / CEPII BACI. Then the Brain tells you which market to cost first.">
        <div className="space-y-5">
          <TradeStatsTool initial={initial} />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=trade" data-testid="pr-open-engine" className="btn-ghost"><ChartLineUp size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <Link to="/intelligence" data-testid="pr-open-intelligence" className="btn-ghost">Market intelligence hub</Link>
          </div>
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
