import React from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import {
  Calculator, Coins, Sparkle, MagnifyingGlass, Users,
  ChartLine, ClipboardText, Robot, ArrowRight,
} from "@phosphor-icons/react";

const TOOLS = [
  { to: "/tools/hsn-finder", label: "HSN Finder", Icon: MagnifyingGlass, desc: "Find the right HSN code with GST, RoDTEP and compliance in seconds." },
  { to: "/tools/duty-calculator", label: "Customs Duty Calculator", Icon: Calculator, desc: "Estimate duty, tax and landed cost in any corridor on earth." },
  { to: "/tools/landed-cost-calculator", label: "Landed Cost Calculator", Icon: Coins, desc: "Detailed cost breakdown — product, freight, insurance, duty and local charges." },
  { to: "/tools/export-incentive-finder", label: "Export Incentive Finder", Icon: Sparkle, desc: "Discover RoDTEP, drawback, MSME subvention and DGFT incentives." },
  { to: "/tools/product-research", label: "Product Research", Icon: ChartLine, desc: "Demand, opportunity and top markets for any product." },
  { to: "/tools/find-buyers", label: "Buyer Discovery", Icon: Users, desc: "Find verified buyers for your product by market and demand." },
  { to: "/tools/export-readiness", label: "Export Readiness Score", Icon: ClipboardText, desc: "Score your export readiness 0–100 and get a personalised roadmap." },
  { to: "/ai-assistant", label: "AI Trade Copilot", Icon: Robot, desc: "Ask anything — HSN, FTAs, certifications, markets. Powered by AI." },
];

export default function ToolsHub() {
  return (
    <>
      <SEO
        title="Free Trade Tools · HSN Finder, Duty Calculator, Buyer Discovery"
        description="LeadNation's free trade toolbox — HSN finder, customs duty calculator, landed cost calculator, export incentive finder, buyer discovery, export readiness score, AI trade copilot."
        path="/tools"
        keywords="free trade tools, HSN finder, customs duty calculator, landed cost calculator, export incentive finder, buyer discovery, export readiness, AI trade assistant"
      />
      <PageHero
        testIdPrefix="tools"
        label="Trade Tools Hub · 100% Free"
        title="Eight tools. One unfair advantage."
        sub="Every tool a global trader needs — HSN, duties, buyers, incentives, readiness — instant, accurate, free. Powered by the LeadNation engine."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {TOOLS.map((t, i) => (
            <Link
              key={t.to}
              to={t.to}
              data-testid={`tools-card-${i}`}
              className="group relative glass rounded-3xl p-6 overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all"
            >
              <div className="absolute -top-20 -right-20 w-44 h-44 rounded-full bg-cyan-500/10 blur-3xl group-hover:bg-cyan-500/20 transition-colors" />
              <div className="relative">
                <div className="w-12 h-12 rounded-xl grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10">
                  <t.Icon size={22} weight="duotone" className="text-cyan-300" />
                </div>
                <h3 className="mt-4 font-display font-bold text-lg leading-tight">{t.label}</h3>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed line-clamp-3">{t.desc}</p>
                <div className="mt-4 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                  Open <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
