import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { BrainExploreCTA } from "@/components/BrainExplore";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { api } from "@/lib/api";
import { ArrowRight, Globe } from "@phosphor-icons/react";

const FAQ = [
  {
    q: "What is a region hub for?",
    a: "It is a shortlist tool. A region hub ranks every market we track inside that region by measured import demand and applied import duty, so you can see in one screen which destinations are worth a tariff deep-dive and which are not — before you open a single product-market guide.",
  },
  {
    q: "Which regions are covered?",
    a: "Europe, the Middle East and Asia Pacific are published as hubs today, covering the markets where we hold both a verified applied tariff and measured import demand. A market only appears inside a hub once it has real data on both counts; we do not pad the list with countries we cannot evidence.",
  },
  {
    q: "Why does a high-demand market sometimes rank below a smaller one?",
    a: "Because demand alone does not pay you. A market that imports twice as much but applies a 30% tariff on your HS code can leave your buyer paying more than a smaller market inside a free trade agreement. The hubs show duty next to demand for exactly this reason.",
  },
  {
    q: "What does 'verified buyer coverage' mean on these pages?",
    a: "It is the count of contact-verified importer records we actually hold for that country, sourced from official trade records — not a company-directory estimate. Where coverage is still being built, the hub says 'buyer coverage expanding' rather than showing a number we cannot stand behind.",
  },
  {
    q: "Does this work for exporters outside India?",
    a: "The duty, landed-cost and demand engines are origin-aware across 56 reporting countries, so the region ranking logic holds for any origin. The published product-market guides are currently written for India as the origin; use the Duty Calculator directly for other origins.",
  },
];

const money = (v) => (!v ? "—" : v >= 1e3 ? `${(v / 1e3).toFixed(0)}k` : `${v}`);

export default function RegionsIndex() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api.get("/seo/regions", { timeout: 120000 }).then(({ data }) => setRows(data.regions || [])).catch(() => {});
  }, []);

  return (
    <div data-testid="regions-index-page">
      <SEO title="Export Regions — Duty, Demand & Buyers by World Region"
        description="Region hubs for exporters: applied import duty, real import demand and verified buyer coverage across Europe, the Middle East and Asia Pacific, with product-market export guides for every tracked market."
        path="/regions"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Regions", path: "/regions" }]}
        faqs={FAQ} />
      <div className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 sm:pt-20 pb-20">
        <div className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">Regions</div>
        <h1 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-3 leading-[1.08]">
          Pick the region, then the <span className="gradient-text">market that pays best</span>
        </h1>
        <p className="mt-5 text-[15px] text-slate-300 max-w-3xl leading-relaxed">
          Each hub ranks its markets by measured import demand and applied import duty, links every published
          product-market guide, and states verified buyer coverage country by country — no filler.
        </p>

        <div className="grid md:grid-cols-3 gap-4 mt-10">
          {rows.map((r) => (
            <Link key={r.slug} to={r.url} data-testid={`regions-card-${r.slug}`}
              className="glass-strong rounded-3xl p-6 hover:border-cyan-400/40 border border-transparent transition-colors group">
              <Globe size={20} weight="duotone" className="text-cyan-300" />
              <h2 className="font-display font-bold text-lg mt-3">{r.name}</h2>
              <div className="text-sm text-slate-400 mt-2">
                {r.countries} markets · {r.guides} export guides
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                {r.buyers ? `${money(r.buyers)} verified buyer records` : "buyer coverage expanding"}
              </div>
              <div className="mt-4 text-sm text-cyan-300 flex items-center gap-1.5">
                Open hub <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>
      <div className="pb-20">
        <AnswerBlock testId="regions-answer" label="Method"
          title="How a market earns its place in a region hub">
          <p>
            A market is only listed once we hold two things for it: an applied import tariff read
            from World Bank WITS / UNCTAD TRAINS at HS6 level, and measured import value from
            OEC World / CEPII BACI. If either is missing for a product-market pair, that pair is
            withheld rather than filled with a sector average.
          </p>
          <p>
            Ranking inside a hub is deliberately two-dimensional. Demand shows you the size of the
            opportunity; applied duty shows you how much of it the destination's customs regime
            takes back. A free trade agreement can move a mid-sized market above a large one for
            your specific HS code, which is why we never publish a single "best market" list.
          </p>
          <p>
            Buyer coverage is reported separately and honestly: it is a count of contact-verified
            importer records we hold for that country. Regions where that work is still in progress
            are labelled as expanding, not inflated.
          </p>
        </AnswerBlock>
        <div className="-mx-6 sm:-mx-10"><BrainExploreCTA kind="region" testIdPrefix="regions-explore" /></div>
        <PageFaq items={FAQ} testIdPrefix="regions-faq" />
      </div>
    </div>
  );
}
