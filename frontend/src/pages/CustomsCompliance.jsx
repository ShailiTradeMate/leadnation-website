import React from "react";
import { useSearchParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
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

export default function CustomsCompliance() {
  const [params, setParams] = useSearchParams();
  const tab = KEYS.includes(params.get("tab")) ? params.get("tab") : "compile";
  const setTab = (k) => { const p = new URLSearchParams(params); p.set("tab", k); setParams(p, { replace: true }); };
  return (
    <>
      <SEO title="Vametra AI Trade Command Center™ — AI Global Trade Operating System"
        description="The world's first AI-powered global trade operating system. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across 195 markets, quote in your currency and any global currency, check duty, FTA benefits, incentives and routes — analysed by the Vametra AI Brain."
        path="/customs-compliance"
        keywords="FOB CIF calculator, landed cost calculator, export costing tool, buyer landed cost comparison, customs duty calculator, FTA checker, RoDTEP incentives, global trade operating system, export quotation tool, dual currency trade quote" />

      <PageHero testIdPrefix="customs" label="Vametra AI Trade Command Center™"
        title="The World's First AI-Powered Global Trade Operating System."
        sub="Plan, cost, comply, price and ship from one screen. Build your full FOB → CIF → landed-cost waterfall, compare buyer landed cost across markets, quote in your currency and any global currency, and let the Vametra AI Brain analyse every number — for any product across 195 countries." />

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

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
