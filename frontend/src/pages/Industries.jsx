import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

export function IndustriesIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/industries").then((r) => setList(r.data)); }, []);
  return (
    <>
      <SEO title="Industry Trade Profiles · 8 sectors, 100+ markets"
        description="Explore India's export profile across agriculture, food, textiles, chemicals, pharma, engineering, handicrafts and FMCG."
        path="/industries"
        keywords="industry export India, agriculture exports, textile exports, pharma exports, engineering exports India"
      />
      <PageHero testIdPrefix="industries" label="Industry Trade Profiles"
        title="Pick your sector. See your edge."
        sub="Sector-level trade intelligence — exports, top markets, compliance and opportunity."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {list.map((i) => (
            <Link key={i.slug} to={`/industries/${i.slug}`} data-testid={`industries-card-${i.slug}`}
              className="group glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
              <div className="h-40 relative overflow-hidden">
                <img src={i.image} alt={i.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
              </div>
              <div className="p-5">
                <h3 className="font-display font-bold text-lg">{i.name}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{i.overview}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function IndustryDetail() {
  const { slug } = useParams();
  const [i, setI] = useState(null);
  const [nf, setNf] = useState(false);
  useEffect(() => { setI(null); setNf(false); api.get(`/industry/${slug}`).then((r) => r.data?.error ? setNf(true) : setI(r.data)).catch(() => setNf(true)); }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">Industry not found</h1><Link to="/industries" className="btn-primary mt-6 inline-flex">Browse industries</Link></div>;
  if (!i) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={`${i.name} Industry · Exports, Markets, Compliance`}
        description={i.overview}
        path={`/industries/${i.slug}`}
        keywords={`${i.name} industry, ${i.name} export India, ${i.name} compliance, ${i.name} markets`}
      />
      <PageHero testIdPrefix="id" label={`Industry · ${i.name}`} title={i.name} sub={i.overview} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-2 gap-5">
        <Card title="Export categories"><div className="mt-3"><ChipList items={i.exports} /></div></Card>
        <Card title="Top markets"><div className="mt-3"><ChipList items={i.topMarkets} variant="violet" /></div></Card>
        <Card title="Compliance" className="lg:col-span-2"><div className="mt-3"><ChipList items={i.compliance} /></div></Card>
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
