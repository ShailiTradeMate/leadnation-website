import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
import { BrainExploreCTA } from "@/components/BrainExplore";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";
import { fetchPageData } from "@/lib/fetchPageData";
import { api } from "@/lib/api";
import {
  ArrowRight, Globe, Scales, Users, Calculator, Brain, SealCheck, MapPin, Package,
} from "@phosphor-icons/react";

const money = (v) => {
  if (!v) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v}`;
};

const Fact = ({ label, value, sub }) => (
  <div className="glass rounded-2xl p-4">
    <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400">{label}</div>
    <div className="font-display font-extrabold text-2xl mt-1.5">{value}</div>
    {sub && <div className="text-[11px] text-slate-400 mt-1">{sub}</div>}
  </div>
);

const CountryCard = ({ c }) => (
  <div className="glass-strong rounded-2xl p-5" data-testid={`region-country-${c.slug}`}>
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h3 className="font-display font-bold text-base truncate">{c.name}</h3>
        <div className="text-[11px] text-slate-400 mt-1">
          {c.topImportsUSD ? `${money(c.topImportsUSD)} ${c.topProduct.toLowerCase()} imports` : "demand data pending"}
          {c.dutyRange && ` · duty ${c.dutyRange.min}%${c.dutyRange.max !== c.dutyRange.min ? `–${c.dutyRange.max}%` : ""}`}
        </div>
      </div>
      {c.buyerCoverage ? (
        <span className="text-[10px] font-mono-display uppercase tracking-wider text-emerald-300 bg-emerald-500/10 border border-emerald-400/20 rounded-full px-2 py-1 shrink-0">
          {c.buyers.toLocaleString()} buyers
        </span>
      ) : (
        <span className="text-[10px] font-mono-display uppercase tracking-wider text-amber-300/80 bg-amber-500/10 border border-amber-400/20 rounded-full px-2 py-1 shrink-0">
          coverage expanding
        </span>
      )}
    </div>

    {c.guides.length > 0 && (
      <div className="mt-4 space-y-1.5">
        {c.guides.map((g) => (
          <Link key={g.url} to={g.url} data-testid={`region-guide-${c.slug}-${g.url.split("/")[2]}`}
            className="flex items-center gap-2 text-[13px] text-slate-300 hover:text-cyan-300 transition-colors">
            <ArrowRight size={12} className="text-cyan-400/70 shrink-0" />
            <span className="truncate">{g.product}</span>
            <span className="ml-auto text-[11px] text-slate-500 shrink-0">{g.dutyRate != null ? `${g.dutyRate}%` : "—"}</span>
          </Link>
        ))}
      </div>
    )}

    <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
      <Link to={c.dutyToolUrl} data-testid={`region-duty-${c.slug}`} className="glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">Duty</Link>
      <Link to={c.landedCostUrl} data-testid={`region-lcc-${c.slug}`} className="glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">Landed cost</Link>
      <Link to={c.buyersUrl} data-testid={`region-buyers-${c.slug}`} className="glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">Buyers</Link>
      {c.profileUrl && <Link to={c.profileUrl} className="glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">Country profile</Link>}
      {c.corridorUrl && <Link to={c.corridorUrl} className="glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">Corridor</Link>}
    </div>
  </div>
);

export default function RegionHub() {
  const { slug } = useParams();
  const [d, setD] = useState(null);
  const [state, setState] = useState("loading");

  useEffect(() => {
    let dead = false;
    setState("loading");
    fetchPageData(`/seo/region/${slug}`).then((res) => {
      if (dead) return;
      if (res.ok) { setD(res.data); setState("ready"); }
      else if (res.notFound) setState("notfound");
      else setState("stalled");
    });
    return () => { dead = true; };
  }, [slug]);

  if (state === "loading" || state === "stalled") {
    const rn = titleize(slug);
    const lfaqs = [
      {
        q: `What does the ${rn} hub show?`,
        a: `Every market we track in ${rn}, ranked by its own measured import demand and showing the applied import duty it charges, with links to each published product-market export guide and the verified buyer coverage we hold for that country.`,
      },
      {
        q: `How is a market selected for inclusion?`,
        a: `A market is only listed once we hold both a verified applied tariff from World Bank WITS / UNCTAD TRAINS and measured import demand from OEC World / CEPII BACI. Pairs where either is missing are withheld rather than filled with a regional average.`,
      },
      {
        q: `Why does a larger market sometimes rank below a smaller one?`,
        a: `Because import volume is not margin. A high-tariff market can leave your buyer paying more than a smaller market inside a trade agreement, and the destination's own VAT or GST compounds the duty because it is charged on the duty-inclusive value.`,
      },
      {
        q: `What does verified buyer coverage mean here?`,
        a: `A count of contact-verified, sanctions-screened importer records we actually hold for that country — not a directory estimate. Where coverage is still being ingested, the hub says so instead of showing a number it cannot stand behind.`,
      },
      {
        q: `Does this work for origins other than India?`,
        a: `The duty, landed-cost and demand engines are origin-aware across the supported reporting countries, so the same ranking logic applies to any origin. The published guides in ${rn} are written for India as the origin; use the Duty Calculator directly for other origins.`,
      },
    ];
    return (
      <div data-testid="region-loading" className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 pb-20">
        <SEO
          title={`Export to ${rn} — Duty, Demand & Buyers by Market`}
          description={`${rn} export hub: applied import duty, measured import demand and verified buyer coverage for every market we track in the region, with product-market export guides.`}
          path={`/regions/${slug}`}
          type="article"
          faqs={lfaqs}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "Regions", path: "/regions" }, { name: rn, path: `/regions/${slug}` }]}
        />
        <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
          <Link to="/regions" className="hover:text-cyan-300">Regions</Link> · {rn}
        </nav>
        <h1 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
          Export to <span className="gradient-text">{rn}</span>
        </h1>
        <p className="mt-5 text-[15px] text-slate-300 max-w-3xl leading-relaxed">
          Loading live duty, demand and buyer-coverage figures for every market in this region.
          Nothing is shown until it has been retrieved from its named source.
        </p>
        <AnswerBlock testId="region-loading-answer" label="Method"
          title={`How a market earns its place in the ${rn} hub`}>
          <p>
            Two dimensions, always together. Measured import demand tells you the size of the
            opportunity in each market; the applied import tariff tells you how much of it the
            destination's customs regime takes back. Published side by side, they usually produce a
            different shortlist from the one an exporter arrives with.
          </p>
          <p>
            Beneath the ranking sits a data gate. A market appears in this hub only when we hold a
            verified applied tariff and measured trade value for it, so the list is shorter than a
            map of the region and every row is defensible.
          </p>
          <p>
            Buyer coverage is reported separately and literally: it is the number of
            contact-verified, sanctions-screened importer records we hold for that country. Markets
            where that work is still in progress are labelled as expanding rather than inflated.
          </p>
        </AnswerBlock>
        <PageFaq items={lfaqs} heading={`Exporting to ${rn} — frequently asked questions`} testIdPrefix="region-loading-faq" />
        <div className="mt-12 flex flex-wrap gap-2 text-sm">
          <Link to="/tools/duty-calculator" className="btn-ghost">Duty calculator</Link>
          <Link to="/tools/landed-cost-calculator" className="btn-ghost">Landed cost calculator</Link>
          <Link to="/export" className="btn-ghost">All export guides</Link>
          <Link to="/regions" className="btn-ghost">All regions</Link>
        </div>
      </div>
    );
  }
  if (state === "notfound" || !d) {
    return (
      <div data-testid="region-error" className="max-w-3xl mx-auto px-5 py-28">
        <SEO title="Region not found" description="This region hub is not available." path={`/regions/${slug}`} noindex />
        <h1 className="font-display font-extrabold text-3xl">We don't publish this region yet</h1>
        <p className="text-slate-400 mt-3 text-sm">
          Try <Link to="/regions" className="text-cyan-300 underline">all regions</Link> or ask the{" "}
          <Link to="/brain" className="text-cyan-300 underline">Vametra AI Brain</Link>.
        </p>
      </div>
    );
  }

  const st = d.stats;
  const answer = `${d.name} covers ${st.countries} markets tracked by Vametra AI, with ${st.guides} ` +
    `product-market export guides backed by real tariff and demand data and ${money(st.importsUSD)} of ` +
    `measured import demand across the tracked products. Verified buyer records are available for ` +
    `${st.buyerCoveredCountries} of ${st.countries} countries in this region.`;

  const faqs = [
    { q: `Which ${d.name} market should I export to first?`, a: `Start where demand and tariff work together. The table on this page ranks ${d.name} markets by measured import demand for each tracked product and shows the applied import duty, so you can see where your landed price lands best before you contact anyone.` },
    { q: `What import duty does ${d.name} charge?`, a: d.facts[0] },
    { q: `Do you have verified buyers in ${d.name}?`, a: `Verified buyer coverage is stated per country on this page — ${st.buyerCoveredCountries} of ${st.countries} ${d.name} markets have screened records today. Where it reads "coverage expanding" we hold none yet and will not show unverified lists.` },
    { q: `Where does this data come from?`, a: d.sources.map((s) => `${s.name} (${s.field})`).join("; ") + ". Every figure carries the reporting year of its source." },
  ];

  const title = `Exporting to ${d.name} — Duty, Demand & Buyers by Country`;
  const description = `Export to ${d.name}: applied import duty, real import demand and verified buyer coverage across ${st.countries} markets, with ${st.guides} product-market guides. Vametra AI.`;

  return (
    <div data-testid="region-hub-page">
      <SEO title={title} description={description} path={d.url} type="article" noindex={!d.indexable} faqs={faqs}
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Regions", path: "/regions" }, { name: d.name, path: d.url }]}
        schema={{
          "@context": "https://schema.org", "@type": "WebPage", name: title, description,
          dateModified: d.generatedAt,
          isPartOf: { "@type": "WebSite", name: "Vametra AI", url: "https://vametra.com" },
        }}
      />

      <div className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 sm:pt-20 pb-20">
        <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
          <Link to="/regions" className="hover:text-cyan-300">Regions</Link> · {d.name} ·{" "}
          <Link to="/export" className="hover:text-cyan-300" data-testid="region-guides-index">All export guides</Link>
        </nav>
        <h1 data-testid="region-h1" className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
          Exporting to <span className="gradient-text">{d.name}</span>
        </h1>
        <p data-testid="region-answer" className="mt-5 text-[15px] sm:text-base text-slate-200 max-w-3xl leading-relaxed">{answer}</p>
        <p className="mt-3 text-sm text-slate-400 max-w-3xl leading-relaxed">{d.intro}</p>
        {!d.indexable && (
          <div data-testid="region-thin-notice" className="mt-4 text-[11px] font-mono-display tracking-wider uppercase text-amber-300/80">{d.indexNote}</div>
        )}

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-8" data-testid="region-snapshot">
          <Fact label="Markets tracked" value={st.countries} sub={`${d.name} coverage`} />
          <Fact label="Export guides" value={st.guides} sub="real tariff + demand data" />
          <Fact label="Import demand" value={money(st.importsUSD)} sub="tracked products, latest year" />
          <Fact label="Buyer coverage" value={`${st.buyerCoveredCountries}/${st.countries}`} sub={`${st.buyerRecords.toLocaleString()} screened records`} />
        </div>

        <section className="mt-14" data-testid="region-facts">
          <div className="flex items-center gap-2.5 mb-4">
            <Scales size={17} weight="duotone" className="text-cyan-300" />
            <h2 className="font-display font-bold text-xl sm:text-2xl">What exporters need to know about {d.name}</h2>
          </div>
          <ul className="space-y-2.5 max-w-3xl">
            {d.facts.map((f, i) => (
              <li key={i} className="flex gap-3 text-sm text-slate-300 leading-relaxed">
                <SealCheck size={16} weight="duotone" className="text-cyan-300 mt-0.5 shrink-0" />{f}
              </li>
            ))}
          </ul>
        </section>

        {d.products.some((p) => p.importsUSD > 0) && (
          <section className="mt-14" data-testid="region-products">
            <div className="flex items-center gap-2.5 mb-4">
              <Package size={17} weight="duotone" className="text-cyan-300" />
              <h2 className="font-display font-bold text-xl sm:text-2xl">Import demand by product</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-3">
              {d.products.filter((p) => p.importsUSD > 0).map((p) => (
                <div key={p.slug} className="glass rounded-2xl p-5" data-testid={`region-product-${p.slug}`}>
                  <div className="flex items-baseline justify-between gap-3">
                    <Link to={`/export/${p.slug}`} data-testid={`region-product-hub-${p.slug}`} className="font-display font-bold text-base hover:text-cyan-300 transition-colors">{p.name}</Link>
                    <span className="font-mono-display text-cyan-300 text-sm">{money(p.importsUSD)}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">{p.sector} · {p.guides} market guide{p.guides === 1 ? "" : "s"}</div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {p.markets.map((m) => (
                      <Link key={m.url} to={m.url} className="text-[11px] glass rounded-full px-2.5 py-1 hover:border-cyan-400/40 transition-colors">
                        {m.country} {m.importsUSD ? money(m.importsUSD) : ""}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="mt-14" data-testid="region-countries">
          <div className="flex items-center gap-2.5 mb-4">
            <MapPin size={17} weight="duotone" className="text-cyan-300" />
            <h2 className="font-display font-bold text-xl sm:text-2xl">{d.name} markets</h2>
          </div>
          <p className="text-sm text-slate-400 mb-4 max-w-3xl">Ranked by published guides and measured import demand. Every card links straight into the duty calculator, landed cost and buyer search for that market.</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {d.countries.map((c) => <CountryCard key={c.slug} c={c} />)}
          </div>
        </section>

        <section className="mt-14 glass-strong rounded-3xl p-6 sm:p-8" data-testid="region-next">
          <div className="flex items-center gap-2.5">
            <Brain size={18} weight="duotone" className="text-cyan-300" />
            <h2 className="font-display font-bold text-lg">Next step for {d.name}</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
            <Link to="/tools/duty-calculator" data-testid="region-cta-duty" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent transition-colors">
              <Calculator size={18} weight="duotone" className="text-cyan-300" />
              <div className="text-sm font-semibold mt-2">Check your duty</div>
              <div className="text-[11px] text-slate-400">Applied and preferential rates for your lane.</div>
            </Link>
            <Link to="/tools/landed-cost-calculator" data-testid="region-cta-lcc" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent transition-colors">
              <Globe size={18} weight="duotone" className="text-cyan-300" />
              <div className="text-sm font-semibold mt-2">Compare landed cost</div>
              <div className="text-[11px] text-slate-400">Rank these markets by what your buyer pays.</div>
            </Link>
            <Link to="/buyers" data-testid="region-cta-buyers" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent transition-colors">
              <Users size={18} weight="duotone" className="text-cyan-300" />
              <div className="text-sm font-semibold mt-2">Find verified buyers</div>
              <div className="text-[11px] text-slate-400">Screened importer records by HS and country.</div>
            </Link>
            <Link to={`/brain?q=${encodeURIComponent(`Which ${d.name} market should I export to first and why?`)}`} data-testid="region-cta-brain" className="glass rounded-2xl p-4 hover:border-cyan-400/40 border border-transparent transition-colors">
              <Brain size={18} weight="duotone" className="text-cyan-300" />
              <div className="text-sm font-semibold mt-2">Ask the Brain</div>
              <div className="text-[11px] text-slate-400">One sourced answer for this region.</div>
            </Link>
          </div>
        </section>

        <div className="-mx-6 sm:-mx-10"><BrainExploreCTA kind="region" defaults={{ region: d.name }} testIdPrefix="region-explore" title={`A product or market in ${d.name} we have not published? The Brain builds it on demand.`} /></div>
        <div className="mt-10 text-[11px] text-slate-500 max-w-3xl leading-relaxed" data-testid="region-sources">
          Sources: {d.sources.map((s) => `${s.name} (${s.field}, as of ${s.asOf})`).join(" · ")}. {d.disclaimer}
        </div>
      </div>
    </div>
  );
}
