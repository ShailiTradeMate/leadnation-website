import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowsLeftRight, ArrowRight, Compass, FileText, Truck, CurrencyCircleDollar } from "@phosphor-icons/react";

export function CorridorsIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/corridors").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO title="Trade Corridors · India to UAE, USA, Australia, Armenia"
        description="Deep-dive trade corridor playbooks — customs, documents, duties and opportunities for every major India lane."
        path="/corridors"
        keywords="India UAE trade corridor, India USA trade, India Australia ECTA, India Armenia EAEU, trade lanes"
      />
      <PageHero testIdPrefix="corridors" label="Trade Corridors"
        title="From your factory to their dock."
        sub="The export and import playbook for every major trade lane — duties, docs, transit time, opportunities."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {list.map((c) => (
            <Link key={c.slug} to={`/corridors/${c.slug}`} data-testid={`corridors-card-${c.slug}`}
              className="group glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
              <div className="h-44 relative overflow-hidden">
                <img src={c.image} alt={`${c.from} to ${c.to}`} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                <div className="absolute top-3 left-3 glass px-3 py-1.5 rounded-full text-sm flex items-center gap-2">
                  <span>{c.fromFlag}</span><ArrowsLeftRight size={14} className="text-cyan-300" /><span>{c.toFlag}</span>
                </div>
              </div>
              <div className="p-5">
                <h3 className="font-display font-bold text-lg">{c.from} → {c.to}</h3>
                <p className="text-sm text-slate-400 mt-1 line-clamp-2">{c.tagline}</p>
                <div className="mt-4 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                  Open corridor <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function CorridorDetail() {
  const { slug } = useParams();
  const [c, setC] = useState(null);
  const [nf, setNf] = useState(false);
  useEffect(() => {
    setC(null); setNf(false);
    api.get(`/corridor/${slug}`).then((r) => r.data?.error ? setNf(true) : setC(r.data)).catch(() => setNf(true));
  }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">Corridor not found</h1><Link to="/corridors" className="btn-primary mt-6 inline-flex">Browse corridors</Link></div>;
  if (!c) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={`${c.from} → ${c.to} Trade Corridor — Customs, Documents, Duties`}
        description={`${c.tagline}. Complete playbook: export process, import process, customs information, documents, duties and opportunities.`}
        path={`/corridors/${c.slug}`}
        keywords={`${c.from} to ${c.to} trade, ${c.from} ${c.to} export, ${c.from} ${c.to} duty, ${c.from} ${c.to} customs`}
      />

      <section className="relative pt-16 pb-10">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
          <SectionLabel>Trade Corridor</SectionLabel>
          <h1 data-testid="cd-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-7xl mt-4 flex flex-wrap items-center gap-3">
            <span>{c.fromFlag}</span> {c.from} <ArrowsLeftRight size={36} className="text-cyan-300 mx-2" /> {c.to} <span>{c.toFlag}</span>
          </h1>
          <p className="mt-4 text-slate-300 text-lg max-w-3xl">{c.tagline}</p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-2 gap-5">
        <Card title="Export Process" Icon={Compass}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{c.exportProcess}</p></Card>
        <Card title="Import Process" Icon={Compass}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{c.importProcess}</p></Card>
        <Card title="Customs Information" Icon={FileText}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{c.customsInfo}</p></Card>
        <Card title="Duties & Taxes" Icon={CurrencyCircleDollar}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{c.dutiesTaxes}</p></Card>
        <Card title="Documentation" Icon={FileText}><ul className="mt-3 space-y-1.5 text-sm">{c.documents.map((d, i) => <li key={i} className="flex gap-2"><ArrowRight size={14} className="text-cyan-300 mt-1" />{d}</li>)}</ul></Card>
        <Card title="Logistics" Icon={Truck}><p className="mt-3 text-slate-300 text-sm leading-relaxed">{c.logistics}</p></Card>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-8 glass-strong rounded-3xl p-7">
        <h2 className="font-display font-bold text-2xl">Trade opportunities</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {c.opportunities.map((o) => <span key={o} className="px-3 py-1.5 rounded-full text-sm bg-cyan-500/10 border border-cyan-400/20">{o}</span>)}
        </div>
      </section>

      {c.popularProducts?.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-8">
          <h2 className="font-display font-bold text-2xl">Popular products in this corridor</h2>
          <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {c.popularProducts.map((p) => (
              <Link key={p} to={`/products/${p}`} className="glass rounded-2xl px-4 py-3 hover:border-cyan-400/30 capitalize text-sm flex items-center justify-between">
                {p.replace(/-/g, " ")}<ArrowRight size={14} className="text-cyan-300" />
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
