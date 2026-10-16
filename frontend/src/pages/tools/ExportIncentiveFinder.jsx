import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
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
      <SEO title="Export Incentive Calculator India: RoDTEP, EPCG | Vametra AI"
        description="Export incentive calculator for India: published RoDTEP rate by HS code from DGFT Appendix 4R, plus duty drawback, EPCG and other official schemes — and the import duty your buyer pays at destination."
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Export Incentive Calculator", path: "/tools/export-incentive-finder" }]}
        path="/tools/export-incentive-finder"
        keywords="export incentives by country, duty drawback, export VAT refund, RoDTEP rate by HS code, export credit insurance, export support schemes, DGFT schemes"
        faqs={FAQ.map(([q, a]) => ({ q, a }))}
      />
      <ToolShell testIdPrefix="inc" label="Export Incentive Finder"
        title="Export incentive calculator India — RoDTEP, drawback, EPCG."
        sub="Pick your product and your trade lane. You get the import duty at destination from WITS, and the official export-support schemes published by your own exporting country — each linked to the authority that administers it. India also returns its published RoDTEP rate.">
        <div className="space-y-6">
          <DutyBenefitsTool initial={initial} focus="benefits" />
          <CountryIncentiveMap />
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
