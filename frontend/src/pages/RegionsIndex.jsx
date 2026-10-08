import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight, Globe } from "@phosphor-icons/react";

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
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Regions", path: "/regions" }]} />
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
    </div>
  );
}
