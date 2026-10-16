import React from "react";
import { useSearchParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
import { PageFaq } from "@/components/PageFaq";
import {
  ShieldCheck, CurrencyCircleDollar, Cube, Path, Gift, Handshake, ChartLineUp, Scales, Lightning,
} from "@phosphor-icons/react";
import {
  CommandCenterTool, ReportTool, TradeStatsTool, DutyBenefitsTool, TradeTermsTool, FxTool, CbmTool, FreightTool, BenefitsTool,
} from "@/components/engines/CustomsEngineTools";

const TABS = [
  ["compile", "Trade Command Center", Lightning],
  ["report", "Compliance Report", ShieldCheck],
  ["trade", "Trade Statistics", ChartLineUp],
  ["duty", "Duty & Benefits", Scales],
  ["terms", "Trade Terms", Handshake],
  ["fx", "Currency Exchange", CurrencyCircleDollar],
  ["cbm", "CBM Calculator", Cube],
  ["freight", "Freight Routes", Path],
  ["benefits", "Govt. Benefits", Gift],
];
const KEYS = TABS.map(([k]) => k);

const CC_FAQ = [
  { q: "What does customs compliance for exporters involve?", a: "Correct HS classification, the applied or preferential duty the destination charges, the documents and rules-of-origin proof required to claim an FTA rate, destination VAT/GST and any restricted-goods or labelling rules. Getting the code wrong invalidates everything downstream." },
  { q: "Where does the duty data come from?", a: "Applied MFN and preferential tariffs are read live from World Bank WITS / UNCTAD TRAINS at HS6 level for {tariffCountries} reporting countries, with the data year shown on every rate." },
  { q: "Can I claim an FTA rate automatically?", a: "No. A preferential rate is conditional on meeting rules of origin and presenting valid origin documentation at clearance. The engine shows the rate; you still have to qualify for it, so price the applied rate unless you can evidence the preferential one." },
  { q: "Does the engine cover imports as well as exports?", a: "Yes. Origin and destination are both yours to set, so the same checks work for an import into your own market or a third-country lane." },
];

export default function CustomsCompliance() {
  const [params, setParams] = useSearchParams();
  const tab = KEYS.includes(params.get("tab")) ? params.get("tab") : "compile";
  const setTab = (k) => { const p = new URLSearchParams(params); p.set("tab", k); setParams(p, { replace: true }); };
  return (
    <>
      <SEO title="Customs Compliance for Exporters: AI Checks | Vametra AI"
        description="Customs compliance for exporters in one engine: HS classification, applied and FTA duty for 56 countries, landed cost waterfall, incentives, documents and routes — analysed by the Vametra AI Brain."
        path="/customs-compliance"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Customs Compliance", path: "/customs-compliance" }]}
        faqs={CC_FAQ}
        keywords="FOB CIF calculator, landed cost calculator, export costing tool, buyer landed cost comparison, customs duty calculator, FTA checker, RoDTEP incentives, global trade operating system, export quotation tool, dual currency trade quote" />

      <PageHero testIdPrefix="customs" label="Vametra AI Trade Command Center™"
        title="Customs compliance for exporters — clearance before cargo moves."
        sub="Plan, cost, comply, price and ship from one screen. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across markets, quote in your currency and any global currency, and let the Vametra AI Brain analyse every number — for any product across 56 tariff-reporting countries." />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
          {TABS.map(([k, label, I]) => (
            <button key={k} data-testid={`customs-tab-${k}`} onClick={() => setTab(k)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm whitespace-nowrap transition-all ${tab === k ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              <I size={15} weight="duotone" />{label}
            </button>
          ))}
        </div>

        {tab === "compile" && <CommandCenterTool />}
        {tab === "report" && <ReportTool />}
        {tab === "trade" && <TradeStatsTool />}
        {tab === "duty" && <DutyBenefitsTool />}
        {tab === "terms" && <TradeTermsTool />}
        {tab === "fx" && <FxTool />}
        {tab === "cbm" && <CbmTool />}
        {tab === "freight" && <FreightTool />}
        {tab === "benefits" && <BenefitsTool />}
      </section>

      <AnswerFirst testId="customs-answer"
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
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
