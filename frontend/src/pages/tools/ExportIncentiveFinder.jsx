import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { DutyBenefitsTool } from "@/components/engines/CustomsEngineTools";
import CountryIncentiveMap from "@/components/CountryIncentiveMap";
import { ArrowSquareOut, Gift } from "@phosphor-icons/react";

const FAQ = [
  ["Does every country give export incentives?", "No. India publishes a rate-level remission schedule (RoDTEP). Most countries support exporters through duty drawback, export VAT refunds, duty-free input regimes, state export credit insurance or market-development grants — and EU/WTO rules prohibit direct export subsidies."],
  ["Why is there no percentage for my country?", "Only a few governments publish an official rate schedule. Where no official rate exists, we name the scheme and link the administering authority instead of showing a number you could not rely on in a contract."],
  ["How current is this?", "Every scheme links to the authority's own page. Scheme names and eligibility change with each budget or trade-policy notification — confirm on the official page before you price an export."],
];

export default function ExportIncentiveFinder() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "", from: p.get("from") || "356", to: p.get("to") || "784" };
  return (
    <>
      <SEO title="Export Incentive Finder · Official Export-Support Schemes by Country"
        description="Find the official export-support schemes your own country publishes — remissions, duty drawback, export VAT refunds, duty-free input regimes, export credit and grants — plus the import duty your buyer pays at destination. 50+ exporting countries, every scheme linked to its authority."
        path="/tools/export-incentive-finder"
        keywords="export incentives by country, duty drawback, export VAT refund, RoDTEP rate by HS code, export credit insurance, export support schemes, DGFT schemes"
        faqs={FAQ.map(([q, a]) => ({ q, a }))}
      />
      <ToolShell testIdPrefix="inc" label="Export Incentive Finder"
        title="What your country gives you — and what your buyer pays."
        sub="Pick your product and your trade lane. You get the import duty at destination from WITS, and the official export-support schemes published by your own exporting country — each linked to the authority that administers it. India also returns its published RoDTEP rate.">
        <div className="space-y-6">
          <DutyBenefitsTool initial={initial} focus="benefits" />
          <CountryIncentiveMap />
          <div className="grid md:grid-cols-3 gap-4" data-testid="inc-faq">
            {FAQ.map(([q, a]) => (
              <div key={q} className="glass rounded-2xl p-5"><div className="font-display font-bold text-sm">{q}</div><p className="text-sm text-slate-400 mt-2 leading-relaxed">{a}</p></div>
            ))}
          </div>
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
