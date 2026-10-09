import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight, Package, Globe, MagnifyingGlass } from "@phosphor-icons/react";

const money = (v) => {
  if (!v) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${(v / 1e3).toFixed(0)}K`;
};

export default function ExportGuidesIndex() {
  const [d, setD] = useState(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.get("/seo/guides", { timeout: 120000 }).then(({ data }) => setD(data)).catch(() => setD({ products: [], regions: [], total: 0 }));
  }, []);

  const products = useMemo(() => {
    if (!d) return [];
    const t = q.trim().toLowerCase();
    if (!t) return d.products;
    return d.products
      .map((p) => ({ ...p, markets: p.markets.filter((m) => m.country.toLowerCase().includes(t)) }))
      .filter((p) => p.markets.length || p.name.toLowerCase().includes(t));
  }, [d, q]);

  return (
    <div data-testid="guides-index-page">
      <SEO title="Export Guides — Every Product and Market We Publish"
        description="Every Vametra AI export guide: applied import duty, real import demand and verified buyer coverage for each product and destination market. Published only where real tariff and demand data exists."
        path="/export"
        keywords="export guide, how to export, import duty by country, export market research, HS code duty by country"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Export guides", path: "/export" }]} />

      <div className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 sm:pt-20 pb-20">
        <div className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-cyan-300">Export guides</div>
        <h1 className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-3 leading-[1.08]">
          {d ? d.total : "—"} market guides, <span className="gradient-text">one per product and destination</span>
        </h1>
        <p className="mt-5 text-[15px] text-slate-300 max-w-3xl leading-relaxed">
          Each guide carries the applied import duty for the lane, that market's real import demand, the documents
          and certifications it asks for, and our verified buyer coverage — stated honestly, including where it is
          still expanding. A product-market pair is only published when real tariff and demand data exists for it.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <div className="relative">
            <MagnifyingGlass size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input data-testid="guides-search" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Find a market or product"
              className="glass rounded-xl pl-9 pr-3 py-2.5 text-sm w-full sm:w-72 outline-none focus:border-cyan-400/40" />
          </div>
          {(d?.regions || []).filter((r) => r.url).map((r) => (
            <Link key={r.slug} to={r.url} data-testid={`guides-region-${r.slug}`}
              className="glass rounded-full px-4 py-2 text-xs hover:border-cyan-400/40 transition-colors">
              <Globe size={13} className="inline mr-1.5 text-cyan-300" />{r.name} · {r.guides}
            </Link>
          ))}
        </div>

        <div className="mt-10 space-y-5">
          {products.map((p) => (
            <section key={p.slug} className="glass-strong rounded-3xl p-6" data-testid={`guides-product-${p.slug}`}>
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400">{p.sector} · HS {p.primaryHs}</div>
                  <h2 className="font-display font-bold text-xl mt-1.5">{p.name}</h2>
                  <div className="text-[11px] text-slate-400 mt-1">{p.marketCount} published markets · {money(p.demandUSD)} measured import demand</div>
                </div>
                <Link to={p.hub} data-testid={`guides-hub-${p.slug}`} className="btn-ghost text-sm">
                  <Package size={14} weight="bold" /> Open product hub <ArrowRight size={13} />
                </Link>
              </div>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {p.markets.map((m) => (
                  <Link key={m.url} to={m.url} data-testid={`guides-link-${p.slug}-${m.countrySlug}`}
                    className="text-[12px] glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">
                    {m.country}
                    <span className="text-slate-500 ml-1.5">{m.dutyRate != null ? `${m.dutyRate}%` : "—"}</span>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>

        {d && (
          <div className="mt-8 text-[11px] text-slate-500">
            Data as of {String(d.dataAsOf || "").slice(0, 10)} · duty from World Bank WITS / UNCTAD TRAINS ·
            demand from OEC World (CEPII BACI / UN Comtrade).
          </div>
        )}
      </div>
    </div>
  );
}
