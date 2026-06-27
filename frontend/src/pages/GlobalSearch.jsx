import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { MagnifyingGlass, ArrowRight } from "@phosphor-icons/react";

const TYPE_COLORS = {
  product: "bg-cyan-500/15 text-cyan-300",
  country: "bg-violet-500/15 text-violet-300",
  corridor: "bg-emerald-500/15 text-emerald-300",
  industry: "bg-amber-500/15 text-amber-300",
  blog: "bg-rose-500/15 text-rose-300",
  hsn: "bg-blue-500/15 text-blue-300",
  service: "bg-fuchsia-500/15 text-fuchsia-300",
  tool: "bg-teal-500/15 text-teal-300",
  supplier: "bg-lime-500/15 text-lime-300",
  buyer: "bg-orange-500/15 text-orange-300",
  faq: "bg-sky-500/15 text-sky-300",
  learning: "bg-indigo-500/15 text-indigo-300",
  compliance: "bg-pink-500/15 text-pink-300",
  scheme: "bg-yellow-500/15 text-yellow-300",
};

export default function GlobalSearch() {
  const [params, setParams] = useSearchParams();
  const initial = params.get("q") || "";
  const [q, setQ] = useState(initial);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const term = (params.get("q") || "").trim();
    if (!term) { setData(null); return; }
    setLoading(true);
    api.get("/brain/search", { params: { q: term } }).then((r) => setData(r.data)).finally(() => setLoading(false));
  }, [params]);

  const submit = (e) => {
    e.preventDefault();
    setParams({ q });
  };

  return (
    <>
      <SEO title={initial ? `Search "${initial}" · LeadNation` : "Search · LeadNation"}
        description="Search products, countries, HSN codes, corridors, services, tools and articles across the LeadNation platform."
        path="/search"
        keywords="LeadNation search, trade search, HSN search, product search"
      />
      <PageHero testIdPrefix="search" label="LeadNation Brain · Universal Search"
        title="Search the entire trade brain."
        sub="One box across countries, products, HSN, corridors, industries, services, suppliers, buyers, learning, FAQs, blogs and tools — ranked by relevance."
      >
        <form onSubmit={submit} className="glass-strong rounded-2xl flex items-center gap-3 px-4 py-3 max-w-2xl">
          <MagnifyingGlass size={20} className="text-cyan-300" />
          <input
            data-testid="search-input" value={q} autoFocus
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search 'rice', 'india', 'HSN 1006', 'IEC'…"
            className="flex-1 bg-transparent outline-none text-white text-[15px] placeholder:text-slate-500"
          />
          <button data-testid="search-submit" className="btn-primary !py-2 !px-4 text-xs">Search</button>
        </form>
      </PageHero>

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        {loading && <div className="text-slate-400">Searching…</div>}
        {data && !loading && (
          <>
            <div className="text-xs text-slate-400 mb-4">{data.total} results for "{data.query}"</div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.results.map((r, i) => (
                <Link key={i} to={r.to} data-testid={`search-result-${i}`}
                  className="glass rounded-2xl p-5 hover:border-cyan-400/30 transition-all flex items-start gap-3 group">
                  <span className={`px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase ${TYPE_COLORS[r.type] || "bg-white/10"}`}>{r.type}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-bold text-sm leading-tight">{r.label}</div>
                    {r.sub && <div className="text-xs text-slate-400 mt-1">{r.sub}</div>}
                  </div>
                  <ArrowRight size={14} className="text-cyan-300 mt-1 shrink-0 group-hover:translate-x-1 transition-transform" />
                </Link>
              ))}
              {data.results.length === 0 && <div className="text-slate-500 col-span-full text-center py-10">No matches. Try a different search term.</div>}
            </div>
          </>
        )}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}
