import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { SealCheck, Lock, ArrowRight } from "@phosphor-icons/react";

const KINDS = [
  { slug: "exporters", label: "Exporters" },
  { slug: "importers", label: "Importers" },
  { slug: "suppliers", label: "Suppliers" },
  { slug: "cha", label: "Customs House Agents (CHA)" },
  { slug: "export-agents", label: "Export Agents" },
];

export function DirectoryHub() {
  return (
    <>
      <SEO title="LeadNation Directories · Exporters, Importers, Suppliers, CHA & Agents"
        description="Verified directories of Indian exporters, global importers, suppliers, customs house agents and export agents — by LeadNation."
        path="/directory"
        keywords="Indian exporters directory, global importers directory, customs house agents India, export agents directory"
      />
      <PageHero testIdPrefix="directory" label="LeadNation Directory"
        title="Verified directories. Verified opportunities."
        sub="Browse the largest, most-trusted directory of exporters, importers, suppliers and trade agents."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {KINDS.map((k) => (
            <Link key={k.slug} to={`/directory/${k.slug}`} data-testid={`directory-card-${k.slug}`}
              className="group glass rounded-3xl p-7 hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Directory</div>
              <h3 className="font-display font-extrabold text-2xl mt-2">{k.label}</h3>
              <div className="mt-5 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                Open directory <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function DirectoryDetail() {
  const { kind } = useParams();
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");

  useEffect(() => {
    api.get(`/directory/${kind}`, { params: { q, country } }).then((r) => setData(r.data)).catch(() => setData({ items: [], total: 0 }));
  }, [kind, q, country]);

  const label = KINDS.find((k) => k.slug === kind)?.label || kind;

  return (
    <>
      <SEO title={`${label} Directory · Verified by LeadNation`}
        description={`Verified ${label.toLowerCase()} directory — searchable by name, country and category. Powered by LeadNation.`}
        path={`/directory/${kind}`}
        keywords={`${label} directory, verified ${label.toLowerCase()}, India ${label.toLowerCase()}`}
      />
      <PageHero testIdPrefix="dirdet" label="Directory" title={label} sub={`Verified ${label.toLowerCase()} — searchable by name, country and category.`} />

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="glass-strong rounded-3xl p-5 flex flex-wrap gap-3">
          <input data-testid="dir-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name or category…" className="flex-1 min-w-[180px] glass rounded-xl px-4 py-3 outline-none" />
          <input data-testid="dir-country" value={country} onChange={(e) => setCountry(e.target.value)} placeholder="Country code (IN, US…)" className="w-44 glass rounded-xl px-4 py-3 outline-none" />
        </div>

        {data && (
          <>
            <div className="mt-6 text-sm text-slate-400">{data.total} results</div>
            <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.items.map((it, i) => (
                <div key={i} data-testid={`dir-card-${i}`} className="glass rounded-3xl p-5">
                  <div className="flex items-center justify-between">
                    <div className="font-display font-bold">{it.name}</div>
                    {it.verified && <SealCheck size={20} weight="fill" className="text-cyan-300" />}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{it.city} · {it.country}</div>
                  <div className="mt-3 text-sm">{it.category}</div>
                  <div className="mt-2 text-[10px] font-mono-display tracking-widest uppercase text-slate-500">
                    Since {it.since}{it.licence ? ` · Lic ${it.licence}` : ""}
                  </div>
                </div>
              ))}
              {data.items.length === 0 && <div className="text-slate-500 col-span-full text-center py-10">No matches.</div>}
            </div>
            {data.lockedExtras && data.items.length > 0 && (
              <div className="mt-6 glass-strong rounded-3xl p-6 flex items-center gap-4 border border-cyan-400/20">
                <Lock size={26} className="text-cyan-300" weight="duotone" />
                <div className="flex-1">
                  <div className="font-display font-bold">10,000+ more profiles inside the LeadNation app.</div>
                  <div className="text-sm text-slate-400">With contact persons, deal history and direct messaging.</div>
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
