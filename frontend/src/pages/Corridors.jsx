import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { BrainExploreCTA } from "@/components/BrainExplore";
import { loadEntity } from "@/lib/fetchPageData";
import { corridorSeo } from "@/data/seoTitles";
import { AnswerFirst } from "@/components/AnswerFirst";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";
import { CountryGuides } from "@/components/LinkGraph";
import { api } from "@/lib/api";
import { ArrowsLeftRight, ArrowRight, Compass, FileText, Truck, CurrencyCircleDollar } from "@phosphor-icons/react";

const INDEX_FAQ = [
  {
    q: "What is a trade corridor page for?",
    a: "A corridor is one origin and one destination treated as a single operating problem: how goods leave, how they clear on arrival, which documents travel with them, what duties and taxes apply, and what the realistic transit time and mode are. It is the operational layer that sits under any product decision.",
  },
  {
    q: "How is a corridor different from a country profile?",
    a: "A country profile describes one market. A corridor describes the movement between two — including the trade agreement that governs it, the origin documentation that agreement demands, and the clearance steps on both sides. Two exporters shipping the same product into the same country from different origins face different corridors.",
  },
  {
    q: "Which corridors are published?",
    a: "The major India lanes are published today, including India to the UAE, the USA, Australia and Armenia. Each one links to every product-market export guide we hold for that destination, so you can move from the corridor mechanics straight to the duty and demand numbers for your specific product.",
  },
  {
    q: "Does a corridor page tell me my duty?",
    a: "It tells you the duty and tax regime that governs the lane. The exact rate is HS-code specific, so use the Customs Duty Calculator with your 6-digit code and the corridor's origin and destination — that returns the applied MFN rate and any preferential rate from World Bank WITS / UNCTAD TRAINS.",
  },
  {
    q: "Can I use these for import rather than export?",
    a: "Yes. Every corridor page sets out both the export process on the origin side and the import clearance process on the destination side, because one party's export problem is the counterparty's import problem and most disputes come from one side not reading the other's half.",
  },
];

export function CorridorsIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/corridors").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO title="India Trade Corridors: Duty, FTA, Shipping | Vametra AI"
        description="Trade corridor playbooks — export process, import clearance, customs documents, duties, taxes and logistics for every major India lane, linked to per-product export guides."
        path="/corridors"
        keywords="India UAE trade corridor, India USA trade, India Australia ECTA, India Armenia EAEU, trade lanes"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Trade Corridors", path: "/corridors" }]}
        faqs={INDEX_FAQ}
      />
      <PageHero testIdPrefix="corridors" label="Trade Corridors"
        title="India trade corridors — duty, FTA and shipping by destination."
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
      <AnswerBlock testId="corridors-answer" label="Why lanes, not countries"
        title="The paperwork is lane-specific, and so is the saving">
        <p>
          Duty is the number everyone looks at first, but on most lanes the money is lost or saved
          in documentation. A preferential tariff under a trade agreement is only available if your
          goods satisfy that agreement's rules of origin and you present a valid origin certificate
          at clearance. Miss the paperwork and you pay the full applied rate on goods that
          technically qualified.
        </p>
        <p>
          Each corridor page therefore puts the export process, the import clearance process, the
          customs regime, the duty and tax treatment, the document set and the logistics profile on
          one page — for one specific origin-destination pair, because none of those are
          transferable between lanes.
        </p>
        <p>
          Rates referenced on corridor pages trace back to World Bank WITS / UNCTAD TRAINS, and
          product-level demand to OEC World / CEPII BACI. For the exact rate on your article, use
          the Duty Calculator with your 6-digit HS code rather than a corridor-level generalisation.
        </p>
      </AnswerBlock>
      <BrainExploreCTA kind="corridor" testIdPrefix="corridors-explore" />
      <PageFaq items={INDEX_FAQ} testIdPrefix="corridors-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function CorridorDetail() {
  const { slug } = useParams();
  const [c, setC] = useState(null);
  const [nf, setNf] = useState(false);
  const [guides, setGuides] = useState(null);
  useEffect(() => {
    setC(null); setNf(false); setGuides(null);
    loadEntity(`/corridor/${slug}`, setC, () => setNf(true));
    const dest = String(slug || "").split("india-to-")[1];
    if (dest) api.get(`/seo/guides-by-country/${dest}`, { timeout: 120000 }).then((r) => setGuides(r.data)).catch(() => {});
  }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><SEO title="Not found" description="This page does not exist." noindex /><h1 className="font-display font-extrabold text-4xl">Corridor not found</h1><Link to="/corridors" className="btn-primary mt-6 inline-flex">Browse corridors</Link></div>;
  if (!c) {
    const n = titleize(slug).replace(/\bIndia To\b/i, "India →");
    return (
      <div className="max-w-7xl mx-auto px-6 py-32">
        <SEO title={String(slug || "").startsWith("india-to-") ? corridorSeo(titleize(String(slug).split("india-to-")[1])).title : `${n} Trade Corridor — Customs, Documents, Duties`}
          description={`${n} trade corridor playbook: export process, import clearance, customs regime, duties and taxes, required documents and logistics — Vametra AI.`}
          path={`/corridors/${slug}`}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "Trade Corridors", path: "/corridors" }, { name: n, path: `/corridors/${slug}` }]} />
        <h1 className="font-display font-extrabold text-4xl">{String(slug || "").startsWith("india-to-") ? corridorSeo(titleize(String(slug).split("india-to-")[1])).h1 : n}</h1>
        <p className="text-slate-400 mt-4 text-sm">Loading…</p>
      </div>
    );
  }

  const docs = (c.documents || []).slice(0, 8).join(", ");
  const faqs = [
    {
      q: `What are the customs requirements for exporting from ${c.from} to ${c.to}?`,
      a: `${c.customsInfo || c.tagline} Clearance on the ${c.to} side and the export formalities on the ${c.from} side are set out in full on this page, because a shipment only moves when both halves are satisfied.`,
    },
    {
      q: `What documents are needed for the ${c.from} to ${c.to} route?`,
      a: `${docs || "The required document set is listed on this page"}. Missing or inconsistent origin documentation is the most common reason a qualifying shipment ends up paying the full applied tariff on this lane.`,
    },
    {
      q: `What duties and taxes apply on the ${c.from}–${c.to} corridor?`,
      a: `${c.dutiesTaxes || "Duty and tax treatment for this lane is described on this page."} The exact rate is HS-code specific, so run your 6-digit code through the Customs Duty Calculator with ${c.from} as origin and ${c.to} as destination to get the applied and any preferential rate from World Bank WITS / UNCTAD TRAINS.`,
    },
    {
      q: `How long does a ${c.from} to ${c.to} shipment take?`,
      a: `${c.logistics || "Transit time and mode options for this lane are described on this page."}`,
    },
    {
      q: `Which products move best from ${c.from} to ${c.to}?`,
      a: `${(c.popularProducts || []).length ? `${(c.popularProducts || []).map((p) => String(p).replace(/-/g, " ")).slice(0, 8).join(", ")} are the established categories on this lane.` : "The established categories on this lane are listed on this page."} Each links to a product-market export guide carrying the applied duty and measured import demand for that exact pair.`,
    },
  ];

  return (
    <>
      <SEO title={c.from === "India" ? corridorSeo(c.to).title : `${c.from} → ${c.to} Trade Corridor — Customs, Documents, Duties`}
        description={`Export from ${c.from} to ${c.to}: ${c.tagline}. Export and import process, customs regime, applied duty and taxes, required documents and logistics, linked to per-product export guides.`}
        path={`/corridors/${c.slug}`}
        keywords={`${c.from} to ${c.to} trade, ${c.from} ${c.to} export, ${c.from} ${c.to} duty, ${c.from} ${c.to} customs`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Trade Corridors", path: "/corridors" },
          { name: `${c.from} → ${c.to}`, path: `/corridors/${c.slug}` },
        ]}
        faqs={faqs}
      />

      <section className="relative pt-16 pb-10">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
          <SectionLabel>Trade Corridor · {c.fromFlag} {c.from} <ArrowsLeftRight size={12} className="inline text-cyan-300 mx-1" /> {c.to} {c.toFlag}</SectionLabel>
          <h1 data-testid="cd-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4 max-w-4xl">
            {c.from === "India" ? corridorSeo(c.to).h1 : `${c.from} → ${c.to} trade corridor — duty, documents and shipping`}
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

      {guides?.total > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-8">
          <CountryGuides data={guides} heading={`Export guides: ${c.from} → ${c.to}`} testIdPrefix="cd-guides" />
        </section>
      )}

      <AnswerBlock testId="cd-answer" label={`${c.from} → ${c.to} · in practice`}
        title={`What to settle before your first ${c.from} to ${c.to} shipment`}>
        <p>
          Classification first. The 6-digit HS code of the exact article decides the applied tariff
          in {c.to}, the certification regime and whether any preferential rate is even available to
          a {c.from} origin. Get this wrong and every downstream number is wrong.
        </p>
        <p>
          Then origin qualification. {c.dutiesTaxes || "Duty treatment on this lane is set out above."} A
          preferential rate is a conditional entitlement, not a default — it requires the goods to
          meet the agreement's rules of origin and the correct origin document to be presented at
          clearance in {c.to}.
        </p>
        <p>
          Then the operational half. {c.logistics || ""} Build the cost waterfall in the Landed Cost
          Calculator so you know what your buyer in {c.to} actually pays once duty, destination tax
          and freight are applied — and only then open buyer conversations, because a quote you
          cannot hold is worse than no quote.
        </p>
      </AnswerBlock>
      <AnswerFirst testId="cd-answer-first" eyebrow={`${c.from} → ${c.to} · direct answer`}
        answer={`To export from ${c.from} to ${c.to}: ${c.tagline}. ${c.customsInfo || ""} The applied duty and any preferential rate for your HS code are read live from World Bank WITS, and each established product on this lane links to an export guide with measured import demand and verified buyer coverage.`}
        rows={[
          { label: "Documents listed", value: String((c.documents || []).length) },
          { label: "Established products", value: String((c.popularProducts || []).length) },
          { label: "Export guides on this lane", value: guides?.total != null ? String(guides.total) : "See below" },
          { label: "Duty source", value: "WITS / TRAINS · HS6" },
        ]}
        source="World Bank WITS / UNCTAD TRAINS; customs authorities of both countries as published"
        links={[
          { to: "/tools/duty-calculator", label: `Duty into ${c.to}` },
          { to: "/tools/landed-cost-calculator", label: "Landed cost calculator" },
          { to: "/tools/find-buyers", label: `Buyers in ${c.to}` },
          { to: "/export", label: "Export guides" },
          { to: "/corridors", label: "All corridors" },
        ]} />
      <BrainExploreCTA kind="corridor" defaults={{ origin: c.from }} testIdPrefix="cd-explore" title={`Shipping ${c.from} → somewhere other than ${c.to}? The Brain builds that corridor on demand.`} />
      <PageFaq items={faqs} heading={`${c.from} → ${c.to} — frequently asked questions`} testIdPrefix="cd-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
