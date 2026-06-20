import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { SealCheck, Lock, ArrowRight } from "@phosphor-icons/react";

export default function Suppliers() {
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");
  const [category, setCategory] = useState("");

  useEffect(() => {
    api.get("/suppliers", { params: { q, country, category } }).then((r) => setData(r.data));
  }, [q, country, category]);

  return (
    <>
      <SEO title="Supplier Discovery · Verified Indian Manufacturers & Exporters"
        description="Discover verified Indian suppliers and manufacturers — by product, category and country. Free preview, full directory in the app."
        path="/suppliers"
        keywords="Indian suppliers, verified manufacturers, supplier discovery India, B2B supplier database"
      />
      <PageHero testIdPrefix="suppliers" label="Supplier Discovery"
        title="Verified suppliers. Verified opportunities."
        sub="Find the right supplier for every product — verified, categorised and ranked by trade performance."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="glass-strong rounded-3xl p-5 flex flex-wrap gap-3">
          <input data-testid="suppliers-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search product or company…" className="flex-1 min-w-[180px] glass rounded-xl px-4 py-3 outline-none" />
          <input data-testid="suppliers-country" value={country} onChange={(e) => setCountry(e.target.value)} placeholder="Country code (IN, US…)" className="w-44 glass rounded-xl px-4 py-3 outline-none" />
          <input data-testid="suppliers-category" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category" className="w-44 glass rounded-xl px-4 py-3 outline-none" />
        </div>

        {data && (
          <>
            <div className="mt-6 text-sm text-slate-400">{data.total} suppliers found</div>
            <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.suppliers.map((s, i) => (
                <div key={i} data-testid={`suppliers-card-${i}`} className="glass rounded-3xl p-5">
                  <div className="flex items-center justify-between">
                    <div className="font-display font-bold">{s.company}</div>
                    {s.verified && <SealCheck size={20} weight="fill" className="text-cyan-300" />}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{s.city} · {s.country}</div>
                  <div className="mt-3 text-sm">{s.products}</div>
                  <div className="text-[10px] font-mono-display tracking-widest uppercase text-slate-500 mt-2">{s.category}</div>
                </div>
              ))}
            </div>
            {data.lockedExtras && (
              <div className="mt-6 glass-strong rounded-3xl p-6 flex items-center gap-4 border border-cyan-400/20">
                <Lock size={26} className="text-cyan-300" weight="duotone" />
                <div className="flex-1">
                  <div className="font-display font-bold">12,000+ verified suppliers inside the app.</div>
                  <div className="text-sm text-slate-400">Including factory addresses, capacity, certifications, sample MOQs and direct chat.</div>
                </div>
                <Link to="/contact" className="btn-primary">Create free account <ArrowRight size={14} weight="bold" /></Link>
              </div>
            )}
          </>
        )}
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}
