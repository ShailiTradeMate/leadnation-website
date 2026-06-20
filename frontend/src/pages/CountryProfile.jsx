import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api, fetchTradeNews, fetchExpos } from "@/lib/api";
import { ArrowRight, TrendUp, TrendDown, Buildings, Compass, Newspaper, CalendarBlank, Storefront, Globe } from "@phosphor-icons/react";

export default function CountryProfile() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [news, setNews] = useState([]);
  const [expos, setExpos] = useState([]);

  useEffect(() => {
    setData(null); setNotFound(false);
    api.get(`/country/${slug}`).then((r) => {
      if (r.data?.error) setNotFound(true);
      else setData(r.data);
    }).catch(() => setNotFound(true));
    fetchTradeNews().then(setNews).catch(() => {});
    fetchExpos().then(setExpos).catch(() => {});
  }, [slug]);

  if (notFound) {
    return (
      <div className="max-w-7xl mx-auto px-6 sm:px-10 py-32 text-center">
        <h1 className="font-display font-extrabold text-4xl">Country not found</h1>
        <p className="text-slate-400 mt-3">We're adding new country profiles every week.</p>
        <Link to="/countries" className="btn-primary mt-6 inline-flex">Browse all countries</Link>
      </div>
    );
  }
  if (!data) {
    return <div className="max-w-7xl mx-auto px-6 sm:px-10 py-32 text-slate-400">Loading profile…</div>;
  }

  const filteredExpos = expos.filter((e) => (data.expoSlugs || []).includes(e.id));

  return (
    <>
      <SEO
        title={`${data.name} Trade Profile — Imports, Exports, Customs & Compliance`}
        description={`${data.tagline}. Discover ${data.name}'s major imports, exports, customs duties, FTA opportunities, trade events and compliance — updated for ${new Date().getFullYear()}.`}
        path={`/countries/${data.slug}`}
        keywords={`${data.name} trade, ${data.name} imports, ${data.name} exports, ${data.name} customs duty, ${data.name} compliance, ${data.name} expo, international trade ${data.name}`}
        schema={{
          "@context": "https://schema.org",
          "@type": "Country",
          name: data.name,
          identifier: data.code,
          description: data.tagline,
        }}
      />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12 sm:pt-24 sm:pb-16">
          <SectionLabel testId="cp-label">Country Trade Profile · {data.code}</SectionLabel>
          <div className="mt-5 flex items-center gap-5">
            <div className="text-7xl sm:text-8xl leading-none">{data.flag}</div>
            <h1 data-testid="cp-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-7xl">
              {data.name}
            </h1>
          </div>
          <p className="mt-4 text-slate-300 text-lg max-w-2xl">{data.tagline}</p>

          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <KV label="Capital" value={data.capital} />
            <KV label="Currency" value={data.currency} />
            <KV label="GDP" value={data.gdp} accent />
            <KV label="Trade Volume" value={data.tradeVolume} accent />
            <KV label="Rank" value={data.rank} small />
          </div>
        </div>
      </section>

      {/* OVERVIEW */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 glass-strong rounded-3xl p-7 sm:p-9">
          <Heading Icon={Globe} text="Country Overview" />
          <p data-testid="cp-overview" className="mt-4 text-slate-300 leading-relaxed">{data.overview}</p>
        </div>
        <div className="glass-strong rounded-3xl p-7 sm:p-9">
          <Heading Icon={Storefront} text="Marketplace Opportunities" />
          <ul className="mt-4 space-y-2.5">
            {data.marketplace.map((m) => (
              <li key={m} className="flex items-start gap-2 text-sm">
                <ArrowRight size={14} className="text-cyan-300 mt-1" />{m}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* IMPORTS / EXPORTS */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid md:grid-cols-2 gap-5 mt-8">
        <div className="glass rounded-3xl p-7">
          <Heading Icon={TrendUp} text="Major Exports" />
          <div className="mt-4 flex flex-wrap gap-2">
            {data.majorExports.map((m) => (
              <span key={m} data-testid={`cp-export-${m}`} className="px-3 py-2 rounded-full text-sm bg-cyan-500/10 border border-cyan-400/20 text-white">{m}</span>
            ))}
          </div>
        </div>
        <div className="glass rounded-3xl p-7">
          <Heading Icon={TrendDown} text="Major Imports" />
          <div className="mt-4 flex flex-wrap gap-2">
            {data.majorImports.map((m) => (
              <span key={m} data-testid={`cp-import-${m}`} className="px-3 py-2 rounded-full text-sm bg-violet-500/10 border border-violet-400/20 text-white">{m}</span>
            ))}
          </div>
        </div>
      </section>

      {/* OPPORTUNITIES */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-8 glass-strong rounded-3xl p-7 sm:p-9">
        <Heading Icon={Buildings} text="Trade Opportunities" />
        <div className="mt-5 grid sm:grid-cols-2 gap-4">
          {data.opportunities.map((o, i) => (
            <div key={i} className="glass rounded-2xl p-5 text-sm text-slate-200">
              <div className="text-cyan-300 font-mono-display text-[10px] tracking-[0.3em] uppercase">Opp · {String(i + 1).padStart(2, "0")}</div>
              <div className="mt-2">{o}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CUSTOMS / COMPLIANCE */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid md:grid-cols-2 gap-5 mt-8">
        <div className="glass rounded-3xl p-7">
          <Heading Icon={Compass} text="Customs Information" />
          <div className="mt-5 space-y-3 text-sm">
            <RowLine label="Average duty" value={data.customs.avgDuty} />
            <RowLine label="Regulator" value={data.customs.regulator} />
            <RowLine label="Portal" value={data.customs.icegate} />
          </div>
          <Link to="/customs-compliance" className="mt-6 inline-flex btn-ghost text-sm">
            Open Customs Engine <ArrowRight size={14} weight="bold" />
          </Link>
        </div>
        <div className="glass rounded-3xl p-7">
          <Heading Icon={Buildings} text="Compliance Information" />
          <ul className="mt-4 space-y-2.5 text-sm text-slate-300">
            {data.compliance.map((c, i) => (
              <li key={i} className="flex items-start gap-2"><ArrowRight size={14} className="text-cyan-300 mt-1" />{c}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* TRADE NEWS */}
      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-12">
        <Heading Icon={Newspaper} text={`Trade News · ${data.name}`} />
        <div className="mt-6 grid md:grid-cols-3 gap-5">
          {news.slice(0, 3).map((n) => (
            <Link to="/trade-news" key={n.id} className="glass rounded-2xl overflow-hidden hover:border-cyan-400/30 transition-all">
              <div className="h-40 relative overflow-hidden">
                <img src={n.image} alt={n.title} className="absolute inset-0 w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] to-transparent" />
              </div>
              <div className="p-5">
                <div className="text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{n.category}</div>
                <div className="mt-2 font-display font-bold text-base leading-tight">{n.title}</div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* TRADE EVENTS */}
      {filteredExpos.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-12">
          <Heading Icon={CalendarBlank} text={`Trade Events in ${data.name}`} />
          <div className="mt-6 grid md:grid-cols-3 gap-5">
            {filteredExpos.map((e) => (
              <Link to="/expo" key={e.id} className="glass rounded-2xl overflow-hidden hover:border-cyan-400/30 transition-all">
                <div className="h-40 relative overflow-hidden">
                  <img src={e.image} alt={e.name} className="absolute inset-0 w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] to-transparent" />
                </div>
                <div className="p-5">
                  <div className="text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{e.category}</div>
                  <div className="mt-2 font-display font-bold text-base leading-tight">{e.name}</div>
                  <div className="mt-1 text-xs text-slate-400">{e.date} · {e.city}</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}

function KV({ label, value, accent = false, small = false }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div>
      <div className={`mt-2 font-display font-bold ${accent ? "text-cyan-300" : ""} ${small ? "text-sm" : "text-xl"}`}>{value}</div>
    </div>
  );
}
function Heading({ Icon, text }) {
  return (
    <div className="flex items-center gap-2">
      <Icon size={20} weight="duotone" className="text-cyan-300" />
      <h2 className="font-display font-bold text-xl sm:text-2xl">{text}</h2>
    </div>
  );
}
function RowLine({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div>
      <div className="font-display font-semibold text-sm">{value}</div>
    </div>
  );
}
