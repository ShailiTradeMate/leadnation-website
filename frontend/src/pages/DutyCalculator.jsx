import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
import { DutyBenefitsTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, ShieldCheck } from "@phosphor-icons/react";

const FAQ = [
  ["Where does the duty rate come from?", "Applied MFN and preferential tariffs are read live from the World Bank WITS / UNCTAD TRAINS database (56 reporting countries, HS6 level) and cached for 7 days. The data year is shown next to every rate."],
  ["Why is my product not found?", "Search by product name (e.g. 'turmeric') or type the 6-digit HS code. If WITS has no record for a country/product pair, we say so instead of guessing."],
  ["Does it show my own country's export benefits?", "Yes. Pick your origin country and the result lists the official export-support schemes that country publishes — duty drawback, export VAT refunds, export credit, grants — each linked to the administering authority. Rates are shown only where a government publishes an official rate schedule (today, India's RoDTEP)."],
];

export default function DutyCalculator() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "", from: p.get("from") || "", to: p.get("to") || "" };
  return (
    <>
      <SEO
        title="Custom Duty Calculator India & 56 Countries | Vametra AI"
        description="Free custom duty calculator for India and 56 reporting countries: applied MFN and FTA rates by HS code from World Bank WITS / UNCTAD TRAINS, destination VAT and official export schemes."
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Custom Duty Calculator", path: "/tools/duty-calculator" }]}
        faqs={FAQ.map(([q, a]) => ({ q, a }))}
        path="/tools/duty-calculator"
        keywords="customs duty calculator, import duty calculator, import duty by HS code, tariff lookup, preferential FTA rate, US Canada import duty, India UAE duty"
        schema={{
          "@context": "https://schema.org", "@type": "WebApplication",
          name: "Vametra AI Customs Duty Calculator", applicationCategory: "BusinessApplication", operatingSystem: "Web",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        }}
      />
      <ToolShell testIdPrefix="duty" label="Customs Duty Calculator"
        title="Custom duty calculator India — real applied tariffs by HS code."
        sub="Pick your product, origin and destination. You get the applied MFN rate, any preferential (FTA) rate for your origin, the destination's own tax breakdown, and the official export-support schemes your exporting country publishes — with the data year and source on every number.">
        <div className="space-y-5">
          <DutyBenefitsTool initial={initial} />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=duty" data-testid="duty-open-engine" className="btn-ghost"><ShieldCheck size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <span className="text-slate-500 text-xs">Same engine — plus Command Center, Trade Statistics, FX, CBM and freight routes.</span>
          </div>
          <div className="grid md:grid-cols-3 gap-4" data-testid="duty-faq">
            {FAQ.map(([q, a]) => (
              <div key={q} className="glass rounded-2xl p-5"><div className="font-display font-bold text-sm">{q}</div><p className="text-sm text-slate-400 mt-2 leading-relaxed">{a}</p></div>
            ))}
          </div>
        </div>
      </ToolShell>
      <AnswerFirst testId="duty-answer"
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
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
