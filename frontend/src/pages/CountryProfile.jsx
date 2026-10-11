import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";
import { CountryGuides } from "@/components/LinkGraph";
import { api, fetchTradeNews, fetchExpos } from "@/lib/api";
import { ArrowRight, TrendUp, TrendDown, Buildings, Compass, Newspaper, CalendarBlank, Storefront, Globe } from "@phosphor-icons/react";

export default function CountryProfile() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [news, setNews] = useState([]);
  const [expos, setExpos] = useState([]);
  const [guides, setGuides] = useState(null);

  useEffect(() => {
    setData(null); setNotFound(false); setGuides(null);
    api.get(`/country/${slug}`).then((r) => {
      if (r.data?.error) setNotFound(true);
      else setData(r.data);
    }).catch(() => setNotFound(true));
    api.get(`/seo/guides-by-country/${slug}`, { timeout: 120000 }).then((r) => setGuides(r.data)).catch(() => {});
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
    const cn = titleize(slug);
    return (
      <div className="max-w-7xl mx-auto px-6 sm:px-10 py-32">
        <SEO
          title={`${cn} Trade Profile — Imports, Exports, Customs & Compliance`}
          description={`${cn} trade profile: major imports and exports, customs duties, trade agreements, compliance and verified buyer coverage — Vametra AI.`}
          path={`/countries/${slug}`}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "Countries", path: "/countries" }, { name: cn, path: `/countries/${slug}` }]}
        />
        <h1 className="font-display font-extrabold text-4xl">{cn} Trade Profile</h1>
        <p className="text-slate-400 mt-4 text-sm">Loading profile…</p>
      </div>
    );
  }

  const filteredExpos = expos.filter((e) => (data.expoSlugs || []).includes(e.id));
  const faqs = [
    {
      q: `What does ${data.name} mainly import and export?`,
      a: `${data.tagline} The import and export categories, the trade agreements ${data.name} is party to and its customs regime are set out on this page, with product-level duty and demand available per HS code through the tools.`,
    },
    {
      q: `How do I calculate customs duty and landed cost for ${data.name}?`,
      a: `Enter your 6-digit HS code in the Duty Calculator and set ${data.name} as the destination. You get the applied MFN rate plus any preferential rate your origin qualifies for, read from World Bank WITS / UNCTAD TRAINS with the data year shown. The Landed Cost Calculator then adds ${data.name}'s own import tax, freight and FX to give the figure your buyer actually pays.`,
    },
    {
      q: `Do I automatically get a lower duty if ${data.name} has a trade agreement with my country?`,
      a: `No. A preferential rate is conditional: the goods must satisfy that agreement's rules of origin and you must present valid origin documentation at clearance in ${data.name}. Price the applied rate as your base case and treat the preferential rate as upside you have to evidence.`,
    },
    {
      q: `How can I find verified buyers in ${data.name}?`,
      a: `Buyer Intelligence holds contact-verified importer records indexed by HS code and market, sourced from official trade records. Coverage for ${data.name} is stated honestly — where we hold no verified records for a product lane, the page says so rather than showing unvetted contacts.`,
    },
    {
      q: `Which products are worth exporting to ${data.name}?`,
      a: `Start from measured demand rather than intuition: run your HS code through Product Research to see whether ${data.name} imports meaningful volume, then check the applied tariff. The published export guides for ${data.name} list each product we hold verified duty and demand data for.`,
    },
    {
      q: `What documents will a shipment into ${data.name} need?`,
      a: `The commercial set — invoice, packing list, bill of lading or airway bill — plus whatever ${data.name} requires for your specific product: certificates of origin to claim preference, and health, phytosanitary or conformity certificates depending on the HS chapter. The corridor page for your origin sets out the full lane-specific list.`,
    },
  ];

  return (
    <>
      <SEO
        title={`${data.name} Trade Profile — Imports, Exports, Customs & Compliance`}
        description={`${data.tagline}. Discover ${data.name}'s major imports, exports, customs duties, FTA opportunities, trade events and compliance — updated for ${new Date().getFullYear()}.`}
        path={`/countries/${data.slug}`}
        keywords={`${data.name} trade, ${data.name} imports, ${data.name} exports, ${data.name} customs duty, ${data.name} compliance, ${data.name} expo, international trade ${data.name}`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Countries", path: "/countries" },
          { name: data.name, path: `/countries/${data.slug}` },
        ]}
        faqs={faqs}
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

      {guides?.total > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12">
          <CountryGuides data={guides} heading={`Export guides for ${guides.country}`} testIdPrefix="cp-guides" />
        </section>
      )}

      <AnswerBlock testId="cp-answer" label={`${data.name} · how to use this profile`}
        title={`What to establish before you ship to ${data.name}`}>
        <p>
          {data.tagline} A market profile is useful for orientation, but nothing here prices your
          shipment. Three things do: the HS code of your exact article, the tariff {data.name}{" "}
          applies to that code from your origin, and {data.name}'s own tax on imports, which is
          charged on the duty-inclusive value and therefore compounds the tariff.
        </p>
        <p>
          Work in that order. Confirm the classification first, because a trade agreement that looks
          generous at chapter level can exclude your specific line. Then check whether your origin
          has preferential access and whether you can actually satisfy the rules of origin — a
          published preferential rate you cannot document is worth nothing at clearance.
        </p>
        <p>
          Only then is demand worth looking at, and only at HS-code level: whether {data.name}{" "}
          imports meaningful volume of your product, read from measured trade data rather than
          inferred from the size of the economy. Where we hold verified duty and demand for a
          product in this market, there is a published export guide linked on this page.
        </p>
      </AnswerBlock>
      <PageFaq items={faqs} heading={`Exporting to ${data.name} — frequently asked questions`} testIdPrefix="cp-faq" />

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
