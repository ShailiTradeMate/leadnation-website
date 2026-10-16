import React from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ToolShell } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerFirst } from "@/components/AnswerFirst";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { TradeStatsTool } from "@/components/engines/CustomsEngineTools";
import { ArrowSquareOut, ChartLineUp } from "@phosphor-icons/react";

const FAQ = [
  {
    q: "Where does the trade data come from?",
    a: "OEC World / CEPII BACI — reconciled bilateral trade statistics built from national customs declarations. You get the latest published year's world trade value for the HS code, the ranked importing and exporting countries with their share, and the multi-year trend. These are measured flows, not survey estimates or projections.",
  },
  {
    q: "Why is the latest year not the current year?",
    a: "Because trade statistics publish on a lag. National customs data has to be reported, reconciled against mirror flows and released, which typically puts the newest complete year one to two years behind. The data year is shown on screen so you always know what period you are reading.",
  },
  {
    q: "Does a big importer mean a good market for me?",
    a: "Not on its own. Import volume tells you demand exists; it says nothing about what your buyer pays at the border. A large importer applying a high tariff to your origin can be worse than a mid-sized market inside a trade agreement, so read this alongside the Duty Calculator before you shortlist.",
  },
  {
    q: "Can I research at 6-digit HS level?",
    a: "Yes — HS6 is the internationally harmonised level these datasets publish at, and it is the right granularity for market selection. National tariff lines extend to 8 or 10 digits, but those are country-specific and only matter at declaration time, not during research.",
  },
  {
    q: "What if my product has no data?",
    a: "Then we say so. Some HS lines are thinly traded or suppressed in the source for confidentiality, and some newer codes have short histories. We do not substitute a chapter average for a missing line, because an invented number is worse than an acknowledged gap when you are committing capital.",
  },
];

export default function ProductResearch() {
  const [p] = useSearchParams();
  const initial = { hs: p.get("hs") || "" };
  return (
    <>
      <SEO title="Export Product Research: Real Import Demand | Vametra AI"
        description="Free export product research tool: top importing countries, world trade value and multi-year trend for any of 5,606 HS codes, from OEC World / CEPII BACI customs data — measured flows, not estimates."
        path="/tools/product-research"
        keywords="export product research, top importing countries by product, world import demand by HS code, trade statistics by product, best export markets"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Tools", path: "/tools" }, { name: "Product Research", path: "/tools/product-research" }]}
        faqs={FAQ}
      />
      <ToolShell testIdPrefix="pr" label="Product Research"
        title="Export product research with real import demand by HS code."
        sub="Pick any product or HS code. We show the latest-year world trade value, the top importing and exporting countries with their share, and the multi-year trend — straight from OEC World / CEPII BACI. Then the Brain tells you which market to cost first.">
        <div className="space-y-5">
          <TradeStatsTool initial={initial} />
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <Link to="/customs-compliance?tab=trade" data-testid="pr-open-engine" className="btn-ghost"><ChartLineUp size={15} weight="bold" /> Open in full Customs & Compliance Engine <ArrowSquareOut size={13} /></Link>
            <Link to="/intelligence" data-testid="pr-open-intelligence" className="btn-ghost">Market intelligence hub</Link>
          </div>
        </div>
      </ToolShell>
      <AnswerFirst testId="pr-answer-first"
        answer="Export product research means checking that a market measurably imports your product before you spend on it. Vametra AI shows, for any of {hsCodes} HS codes, the latest published world trade value, the ranked importing and exporting countries with share, and the multi-year trend — from OEC World / CEPII BACI, built from national customs declarations."
        rows={[
          { label: "HS codes researchable", value: "{hsCodes}" },
          { label: "Data type", value: "Measured bilateral flows" },
          { label: "Granularity", value: "HS6 · latest published year + trend" },
          { label: "Published export guides", value: "{guides}" },
        ]}
        source="OEC World (CEPII BACI / UN Comtrade)"
        links={[
          { to: "/tools/duty-calculator", label: "Check duty for the top markets" },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/export", label: "Export guides by product" },
          { to: "/regions/middle-east", label: "Middle East export hub" },
          { to: "/tools/find-buyers", label: "Find verified buyers" },
        ]} />
      <AnswerBlock testId="pr-answer" label="Reading the output"
        title="Demand ranking is a shortlist, not an answer">
        <p>
          Import value answers one question well: does this market buy meaningful quantities of my
          product at all. That is enough to eliminate most of the world, which is the expensive part
          of market selection and the part exporters usually skip.
        </p>
        <p>
          What it cannot tell you is margin. Two markets with identical import volumes can differ by
          twenty points of applied tariff, and the destination's VAT or GST on imports is charged on
          the duty-inclusive value, so it compounds whatever the duty does. Take the top five
          markets from here, then price each in the Duty Calculator and the Landed Cost Calculator.
        </p>
        <p>
          Also read the trend, not just the latest year. A market with moderate volume and five
          years of consistent growth is usually an easier entry than a larger market that has been
          contracting — incumbents in a shrinking market defend on price, and a new exporter rarely
          wins that fight.
        </p>
      </AnswerBlock>
      <PageFaq items={FAQ} testIdPrefix="pr-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
