import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";
import { fetchPageData } from "@/lib/fetchPageData";
import { api } from "@/lib/api";
import {
  ArrowRight, Scales, Users, Calculator, Brain, MagnifyingGlass, Package, Globe, TrendUp,
} from "@phosphor-icons/react";

const money = (v) => {
  if (!v) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${(v / 1e3).toFixed(0)}K`;
};

const Fact = ({ label, value, sub }) => (
  <div className="glass rounded-2xl p-4">
    <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400">{label}</div>
    <div className="font-display font-extrabold text-2xl mt-1.5">{value}</div>
    {sub && <div className="text-[11px] text-slate-400 mt-1">{sub}</div>}
  </div>
);

export default function ExportProductHub() {
  const { product } = useParams();
  const [d, setD] = useState(null);
  const [state, setState] = useState("loading");

  useEffect(() => {
    let dead = false;
    setState("loading");
    fetchPageData(`/seo/product-hub/${product}`).then((res) => {
      if (dead) return;
      if (res.ok) { setD(res.data); setState("ready"); }
      else if (res.notFound) setState("notfound");
      else setState("stalled");
    });
    return () => { dead = true; };
  }, [product]);

  if (state === "loading" || state === "stalled") {
    const pn = titleize(product);
    const lfaqs = [
      {
        q: `Which market should I export ${pn} to first?`,
        a: `Shortlist on two numbers together, never one: the measured import demand of each market and the applied import duty it charges on this HS code. A smaller market inside a trade agreement frequently pays you better than a large market applying a double-digit tariff. This hub ranks every published market on both.`,
      },
      {
        q: `What is the HS code for ${pn}?`,
        a: `This hub states the primary HS line we track for ${pn}, plus any related codes. The first six digits are harmonised worldwide and are the right level for market research; your declaration will use the destination's own 8 or 10-digit national line.`,
      },
      {
        q: `How current is the duty and demand data?`,
        a: `Applied tariffs come from World Bank WITS / UNCTAD TRAINS and import demand from OEC World (CEPII BACI / UN Comtrade). Both publish with a lag, so every figure carries its reporting year. Where a source holds no record for a product-market pair, we withhold the guide rather than estimate it.`,
      },
      {
        q: `Why are some markets missing from this hub?`,
        a: `A market is only published once we hold a verified applied tariff and measured import demand for this product. That gate keeps the hub honest, and it is why the market count here is smaller than the number of countries that theoretically import ${pn}.`,
      },
      {
        q: `What do I do after shortlisting a market?`,
        a: `Open that market's guide for the documents, certifications and buyer coverage, then build the cost waterfall in the Landed Cost Calculator so you know what the buyer actually pays landed. Only then is outreach worth the effort.`,
      },
    ];
    return (
      <div data-testid="hub-loading" className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 pb-20">
        <SEO
          title={`Export ${pn} — Markets, Duty, Demand & Buyers`}
          description={`Export ${pn}: applied import duty and real import demand for every published market, plus verified buyer coverage. Vametra AI.`}
          path={`/export/${product}`}
          type="article"
          faqs={lfaqs}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "Export guides", path: "/export" }, { name: pn, path: `/export/${product}` }]}
        />
        <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
          <Link to="/export" className="hover:text-cyan-300">Export guides</Link> · {pn}
        </nav>
        <h1 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
          Export <span className="gradient-text">{pn}</span>
        </h1>
        <p className="mt-5 text-[15px] text-slate-300 max-w-3xl leading-relaxed">
          Loading the published market list with applied duty, measured import demand and verified
          buyer coverage for each. Nothing is shown until it has been retrieved from its source.
        </p>
        <AnswerBlock testId="hub-loading-answer" label="How this hub works"
          title={`Choosing a market for ${pn} on evidence rather than instinct`}>
          <p>
            Exporters usually pick a destination because they have heard of a buyer there, then
            discover the tariff afterwards. This hub inverts that: every market we publish for{" "}
            {pn} is listed with its own measured import demand and the applied duty it charges on
            this HS code, so the shortlist is made before anyone is contacted.
          </p>
          <p>
            Demand and duty have to be read together. A market that imports heavily but applies a
            high tariff to Indian origin can leave your buyer paying more than a mid-sized market
            inside a free trade agreement — and the destination's own VAT or GST, charged on the
            duty-inclusive value, widens that gap further.
          </p>
          <p>
            A market only appears here once we hold both a verified tariff and measured demand for
            it. Where either is missing, the pair is withheld rather than filled with a chapter
            average, because an invented number is worse than an acknowledged gap when you are
            committing working capital.
          </p>
        </AnswerBlock>
        <PageFaq items={lfaqs} heading={`Exporting ${pn} — frequently asked questions`} testIdPrefix="hub-loading-faq" />
        <div className="mt-12 flex flex-wrap gap-2 text-sm">
          <Link to="/tools/duty-calculator" className="btn-ghost">Duty calculator</Link>
          <Link to="/tools/landed-cost-calculator" className="btn-ghost">Landed cost calculator</Link>
          <Link to="/tools/product-research" className="btn-ghost">World demand</Link>
          <Link to="/export" className="btn-ghost">All export guides</Link>
        </div>
      </div>
    );
  }
  if (state === "notfound" || !d) {
    return (
      <div data-testid="hub-error" className="max-w-3xl mx-auto px-5 py-28">
        <SEO title="Product not found" description="This product hub is not published." path={`/export/${product}`} noindex />
        <h1 className="font-display font-extrabold text-3xl">We don't publish this product yet</h1>
        <p className="text-slate-400 mt-3 text-sm">See <Link to="/export" className="text-cyan-300 underline">all export guides</Link>.</p>
      </div>
    );
  }

  const st = d.stats;
  const answer = `Vametra AI publishes ${st.markets} export markets for ${d.name} (HS ${d.primaryHs}), covering ` +
    `${money(st.demandUSD)} of measured import demand. Applied import duty across those markets runs from ` +
    `${st.dutyMin}% to ${st.dutyMax}%, and ${st.zeroDutyMarkets} of them currently report 0% duty on this product.`;

  const faqs = [
    { q: `Which country should I export ${d.name} to?`, a: `The table below ranks every published market by measured import demand and shows the applied import duty for each, so you can shortlist on demand and tariff together before contacting anyone. ${st.zeroDutyMarkets} markets report 0% duty today.` },
    { q: `What is the HS code for ${d.name}?`, a: `Vametra AI uses HS ${d.primaryHs}${d.hsCodes.length > 1 ? ` (also ${d.hsCodes.filter((h) => h !== d.primaryHs).join(", ")})` : ""}. The first 6 digits are harmonised worldwide; confirm the 8 or 10-digit national code in the destination tariff.` },
    { q: `How current is the duty data?`, a: `Applied tariffs come from World Bank WITS / UNCTAD TRAINS and demand from OEC World (CEPII BACI / UN Comtrade). Both publish with a lag, and every guide shows the reporting year next to the figure.` },
  ];

  const title = `Export ${d.name} — ${st.markets} Markets, Duty, Demand & Buyers`;
  const description = `Export ${d.name} (HS ${d.primaryHs}): applied import duty and real import demand for ${st.markets} markets, ${money(st.demandUSD)} measured demand, plus verified buyer coverage. Vametra AI.`;

  return (
    <div data-testid="product-hub-page">
      <SEO title={title} description={description} path={d.url} type="article" faqs={faqs}
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Export guides", path: "/export" }, { name: d.name, path: d.url }]}
        schema={{
          "@context": "https://schema.org", "@type": "WebPage", name: title, description,
          isPartOf: { "@type": "WebSite", name: "Vametra AI", url: "https://vametra.com" },
        }} />

      <div className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 sm:pt-20 pb-20">
        <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
          <Link to="/export" className="hover:text-cyan-300">Export guides</Link> · {d.name}
        </nav>
        <h1 data-testid="hub-h1" className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
          Export <span className="gradient-text">{d.name}</span>
        </h1>
        <p data-testid="hub-answer" className="mt-5 text-[15px] sm:text-base text-slate-200 max-w-3xl leading-relaxed">{answer}</p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-8" data-testid="hub-snapshot">
          <Fact label="Published markets" value={st.markets} sub={`${d.sector}`} />
          <Fact label="Import demand" value={money(st.demandUSD)} sub="latest reported year" />
          <Fact label="Duty range" value={`${st.dutyMin}–${st.dutyMax}%`} sub={`${st.zeroDutyMarkets} markets at 0%`} />
          <Fact label="Verified buyers" value={st.buyerRecords.toLocaleString()} sub="screened importer records" />
        </div>

        <div className="mt-6 flex flex-wrap gap-2 text-sm" data-testid="hub-tools">
          <Link to={d.tools.dutyCalculator} data-testid="hub-tool-duty" className="btn-ghost"><Calculator size={14} weight="bold" /> Duty for your lane</Link>
          <Link to={d.tools.landedCost} data-testid="hub-tool-lcc" className="btn-ghost"><Scales size={14} weight="bold" /> Landed cost</Link>
          <Link to={d.tools.productResearch} data-testid="hub-tool-research" className="btn-ghost"><TrendUp size={14} weight="bold" /> World demand</Link>
          <Link to={d.tools.hsnFinder} data-testid="hub-tool-hsn" className="btn-ghost"><MagnifyingGlass size={14} weight="bold" /> HS code check</Link>
          <Link to={d.tools.buyers} data-testid="hub-tool-buyers" className="btn-ghost"><Users size={14} weight="bold" /> Verified buyers</Link>
          <Link to={d.tools.brain} data-testid="hub-tool-brain" className="btn-ghost"><Brain size={14} weight="bold" /> Ask the Brain</Link>
          {d.marketingProduct && <Link to={d.marketingProduct} data-testid="hub-marketing-link" className="btn-ghost"><Package size={14} weight="bold" /> Product overview</Link>}
        </div>

        <section className="mt-14" data-testid="hub-markets">
          <h2 className="font-display font-bold text-xl sm:text-2xl">Every published market for {d.name}</h2>
          <p className="text-sm text-slate-400 mt-2 mb-5 max-w-3xl">Ranked by that market's own import demand. Duty is the applied rate reported for the destination; open a guide for documents, certifications, FTA status and buyers.</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {d.markets.map((m) => (
              <div key={m.url} className="glass-strong rounded-2xl p-5" data-testid={`hub-market-${m.countrySlug}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Link to={m.url} className="font-display font-bold text-base hover:text-cyan-300 transition-colors truncate block">{m.country}</Link>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {m.importsUSD ? `${money(m.importsUSD)} imports` : "demand pending"}
                      {m.rank ? ` · #${m.rank} worldwide` : ""}
                    </div>
                  </div>
                  <span className="font-mono-display text-sm text-cyan-300 shrink-0">{m.dutyRate != null ? `${m.dutyRate}%` : "—"}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                  <Link to={m.url} data-testid={`hub-guide-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">Guide</Link>
                  <Link to={m.dutyToolUrl} data-testid={`hub-duty-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">Duty</Link>
                  <Link to={m.landedCostUrl} data-testid={`hub-landed-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">Landed cost</Link>
                  <Link to={m.buyersUrl} data-testid={`hub-buyers-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">Buyers</Link>
                  {m.regionHub && <Link to={m.regionHub} data-testid={`hub-market-region-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">{m.region.replace("-", " ")}</Link>}
                  {m.corridor && <Link to={m.corridor} data-testid={`hub-market-corridor-${m.countrySlug}`} className="glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">Corridor</Link>}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 grid md:grid-cols-2 gap-5">
          <div className="glass rounded-3xl p-6" data-testid="hub-regions">
            <div className="flex items-center gap-2 mb-3"><Globe size={16} weight="duotone" className="text-cyan-300" /><h2 className="font-display font-bold text-lg">By region</h2></div>
            <div className="flex flex-wrap gap-2">
              {d.regions.map((r) => (
                <Link key={r.slug} to={r.url} data-testid={`hub-region-${r.slug}`} className="glass rounded-full px-3.5 py-2 text-sm hover:border-cyan-400/40 transition-colors">
                  {r.name} <span className="text-slate-500">{r.markets}</span>
                </Link>
              ))}
            </div>
          </div>
          <div className="glass rounded-3xl p-6" data-testid="hub-related">
            <div className="flex items-center gap-2 mb-3"><Package size={16} weight="duotone" className="text-cyan-300" /><h2 className="font-display font-bold text-lg">Other products</h2></div>
            <div className="flex flex-wrap gap-2">
              {d.relatedProducts.map((r) => (
                <Link key={r.slug} to={r.url} data-testid={`hub-related-${r.slug}`} className="glass rounded-full px-3.5 py-2 text-sm hover:border-cyan-400/40 transition-colors">{r.name}</Link>
              ))}
            </div>
          </div>
        </section>

        <div className="mt-10 text-[11px] text-slate-500 max-w-3xl leading-relaxed" data-testid="hub-sources">
          Sources: {d.sources.map((s) => `${s.name} (${s.field}, as of ${s.asOf})`).join(" · ")}. {d.disclaimer}{" "}
          <Link to="/export" className="text-cyan-300 hover:underline inline-flex items-center gap-1">All export guides <ArrowRight size={11} /></Link>
        </div>
      </div>
    </div>
  );
}
