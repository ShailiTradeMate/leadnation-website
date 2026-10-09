import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
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
    api.get(`/seo/product-hub/${product}`, { timeout: 120000 })
      .then(({ data }) => { if (!dead) { setD(data); setState("ready"); } })
      .catch(() => { if (!dead) setState("error"); });
    return () => { dead = true; };
  }, [product]);

  if (state === "loading") return <div data-testid="hub-loading" className="max-w-7xl mx-auto px-5 sm:px-10 py-28 text-slate-400">Loading published markets…</div>;
  if (state === "error" || !d) {
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
