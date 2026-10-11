import React from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import {
  Calculator, Coins, Sparkle, MagnifyingGlass, Users,
  ChartLine, ClipboardText, Robot, ArrowRight,
} from "@phosphor-icons/react";

const FAQ = [
  {
    q: "Are these tools really free?",
    a: "Yes, and without a signup wall. The HSN Finder, Duty Calculator, Landed Cost Calculator, Export Incentive Finder, Product Research, Buyer Discovery and Export Readiness Score all run on the open site. Saving work as a Trade Project in the Command Center is the part that needs an account.",
  },
  {
    q: "Where does the data behind the tools come from?",
    a: "Applied and preferential tariffs from World Bank WITS / UNCTAD TRAINS at HS6 level across 56 reporting countries. Trade values and demand rankings from OEC World / CEPII BACI. HS classification from WCO HS-2022. Export-support schemes from the administering authorities themselves, including DGFT Appendix 4R for India. Buyer records from Vametra Buyer Intelligence.",
  },
  {
    q: "Which tool should I start with?",
    a: "If you do not yet know your HS code, start with the HSN Finder — every other tool keys off it. If you have the code and a market in mind, start with the Duty Calculator. If you have several candidate markets, start with Product Research to rank real demand, then cost the shortlist in the Landed Cost Calculator.",
  },
  {
    q: "Do the tools work for countries other than India?",
    a: "The duty, landed-cost, HS and demand tools are fully origin and destination aware, so any lane between supported reporting countries works. Export incentives are the exception by necessity: a scheme is only shown where the exporting country publishes an official rate schedule, so you will see rates for some origins and scheme names without rates for others.",
  },
  {
    q: "Is the same engine behind the tools and the full platform?",
    a: "Yes. Each tool is a focused entry point into the same Customs & Compliance Engine, Buyer Intelligence and Vametra AI Brain that power the Command Center. There is no separate 'lite' dataset — a rate you see in the free Duty Calculator is the rate the platform uses.",
  },
  {
    q: "How current are the numbers?",
    a: "Tariff lookups are read live and cached for seven days, with the source data year displayed next to every rate — tariff databases publish on a lag, so the year matters. Trade statistics follow their provider's latest published year. Where a source holds no record for a pair, the tool says so rather than estimating.",
  },
];

const TOOLS = [
  { to: "/tools/hsn-finder", label: "HSN Finder", Icon: MagnifyingGlass, desc: "All 5,606 HS codes with live import duty at your destination and the export support your own country gives.", data: "WCO HS-2022 · WITS · official authorities" },
  { to: "/tools/duty-calculator", label: "Customs Duty Calculator", Icon: Calculator, desc: "Real MFN & preferential tariffs for 56 countries, destination tax breakdown, origin-aware export support.", data: "World Bank WITS / UNCTAD TRAINS" },
  { to: "/tools/landed-cost-calculator", label: "Landed Cost Calculator", Icon: Coins, desc: "Ex-Works → FOB → CIF → landed with live duty, VAT and FX; compare buyer cost across markets.", data: "Trade Command Center engine" },
  { to: "/tools/export-incentive-finder", label: "Export Incentive Finder", Icon: Sparkle, desc: "Official export-support schemes in 50+ exporting countries, plus the duty your buyer pays.", data: "Official authorities · DGFT Appendix 4R · WITS" },
  { to: "/tools/product-research", label: "Product Research", Icon: ChartLine, desc: "Who imports your product: world trade value, top importers/exporters and 5-year trend.", data: "OEC World / CEPII BACI" },
  { to: "/tools/find-buyers", label: "Buyer Discovery", Icon: Users, desc: "27,000+ verified importer records by HS code and market, with trust scores.", data: "Vametra Buyer Intelligence" },
  { to: "/tools/export-readiness", label: "Export Readiness Score", Icon: ClipboardText, desc: "Score your export readiness 0–100 and get a personalised roadmap from the Brain.", data: "Vametra AI Brain" },
  { to: "/brain", label: "Vametra AI Brain", Icon: Robot, desc: "Ask anything — HSN, FTAs, certifications, markets — grounded in the same live engines.", data: "AI Brain" },
];

export default function ToolsHub() {
  return (
    <>
      <SEO
        title="Free Trade Tools · HSN Finder, Duty Calculator, Buyer Discovery"
        description="Vametra AI's free trade toolbox — HSN finder, customs duty calculator, landed cost calculator, export incentive finder, buyer discovery, export readiness score, AI trade copilot. Real WITS, OEC and official-authority data, no signup."
        path="/tools"
        keywords="free trade tools, HSN finder, customs duty calculator, landed cost calculator, export incentive finder, buyer discovery, export readiness, AI trade assistant"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }]}
        faqs={FAQ}
      />
      <PageHero
        testIdPrefix="tools"
        label="Trade Tools Hub · 100% Free"
        title="Eight tools. One engine. Real data on every screen."
        sub="HSN, duties, landed cost, demand, buyers, incentives, readiness — every result comes from the live Customs & Compliance Engine and Buyer Intelligence, and the Vametra AI Brain tells you the next step. Free, no signup."
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
                <div className="mt-3 text-[10px] font-mono-display uppercase tracking-widest text-cyan-300/80" data-testid={`tools-card-${i}-source`}>{t.data}</div>
                <div className="mt-4 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                  Open <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <AnswerBlock testId="tools-answer" label="How these fit together"
        title="One sequence, eight entry points">
        <p>
          Most export decisions fail on the same four unknowns: the HS code, the duty the buyer
          pays, whether that market genuinely imports your product, and what the shipment actually
          costs landed. Each tool here answers exactly one of those, using the same underlying
          engine, so results carry across from one screen to the next.
        </p>
        <p>
          The working order is: classify in the HSN Finder, price the tariff in the Duty Calculator,
          test demand in Product Research, build the waterfall in the Landed Cost Calculator, claim
          what your own country offers in the Export Incentive Finder, and only then open Buyer
          Discovery. The Export Readiness Score is worth running first if this is your first
          shipment, because it surfaces the registrations and certifications that take weeks.
        </p>
        <p>
          Every figure is sourced and dated on screen. Tariffs trace to World Bank WITS /
          UNCTAD TRAINS, demand to OEC World / CEPII BACI, classification to WCO HS-2022, and
          incentive rates to the administering authority. Nothing is modelled, and where a source
          has no record for a pair the tool states that instead of guessing.
        </p>
      </AnswerBlock>
      <PageFaq items={FAQ} testIdPrefix="tools-faq" />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}
