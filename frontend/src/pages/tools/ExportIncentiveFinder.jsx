import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { DutyBenefitsTool, BenefitsTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, Gift } from "@phosphor-icons/react";

export default function ExportIncentiveFinder() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "", from: "356", to: p.get("to") || "784" };
  return (
    <>
      <SEO title="Export Incentive Finder · RoDTEP Rate by HS Code + DGFT Schemes"
        description="Find the DGFT RoDTEP rate for your HS code, the import duty your buyer pays at destination, and the Indian export schemes you can stack — Duty Drawback, EPCG, Advance Authorisation, Interest Equalisation, MAI."
        path="/tools/export-incentive-finder"
        keywords="RoDTEP rate by HS code, export incentives India, DGFT schemes, duty drawback, EPCG scheme, advance authorisation, interest equalisation scheme"
      />
      <ToolShell testIdPrefix="inc" label="Export Incentive Finder"
        title="What India refunds you — and what your buyer pays."
        sub="Search your product. You get the DGFT RoDTEP rate (Appendix 4R) as % of FOB, the destination's live import duty from WITS, and every government scheme you can stack on top. Origin is fixed to India; pick any destination.">
        <div className="space-y-6">
          <DutyBenefitsTool initial={initial} focus="benefits" />
          <BenefitsTool />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=benefits" data-testid="inc-open-engine" className="btn-ghost"><Gift size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <Link to="/services" data-testid="inc-open-services" className="btn-ghost">Get help claiming incentives (Services)</Link>
          </div>
        </div>
      </ToolShell>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
