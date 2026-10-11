import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

const INDEX_FAQ = [
  {
    q: "What does an industry trade profile actually contain?",
    a: "Each sector page lists the export categories that sit inside that industry, the markets that import the most of it, and the compliance regimes a shipment has to clear — certification bodies, product standards and documentation. It is the sector-level view you read before you pick a single product and a single destination.",
  },
  {
    q: "Which sectors does Vametra AI track?",
    a: "Eight: agriculture, food processing, textiles, chemicals, pharmaceuticals, engineering, handicrafts and FMCG. These cover the bulk of India's non-petroleum merchandise export value and map onto the HS chapters our duty, demand and buyer engines already index.",
  },
  {
    q: "How do I get from a sector to an actual export decision?",
    a: "A sector tells you where the demand sits; it cannot tell you what you will be paid or what duty your buyer absorbs. From any industry page, open the matching product profile, then the product-market export guide for a specific destination. That guide carries the applied tariff, measured import demand and verified buyer coverage for that exact lane.",
  },
  {
    q: "Is the compliance information specific to my destination?",
    a: "No — on this page it is sector-wide. Destination-specific requirements change by market, so country-level documentation, labelling and certification sit on the corridor pages and the product-market guides, which are built per destination rather than per sector.",
  },
  {
    q: "Does the same sector logic apply if I am not exporting from India?",
    a: "The tools do. Our duty, landed-cost and demand engines are origin-aware and work for any of 56 reporting countries, so you can run the same sector analysis on a non-India lane. The incentive data is the one exception: export-support schemes are only shown where the exporting country publishes an official rate schedule.",
  },
];

export function IndustriesIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/industries").then((r) => setList(r.data)); }, []);
  return (
    <>
      <SEO title="Industry Trade Profiles · 8 sectors, 100+ markets"
        description="Explore India's export profile across agriculture, food, textiles, chemicals, pharma, engineering, handicrafts and FMCG — export categories, top importing markets and the compliance each sector has to clear."
        path="/industries"
        keywords="industry export India, agriculture exports, textile exports, pharma exports, engineering exports India"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Industries", path: "/industries" }]}
        faqs={INDEX_FAQ}
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
      <AnswerBlock testId="industries-answer" label="How to read these pages"
        title="Start at the sector, finish at a single lane">
        <p>
          Sector data is useful for direction, not for pricing. An industry page shows you which
          product families are already moving and which markets absorb them, so you can rule out
          the categories you cannot supply before you spend time on tariff research.
        </p>
        <p>
          The moment you have a candidate category, the decision becomes lane-specific: the applied
          import duty, the destination's own tax stack, the measured import demand for that HS code
          and whether verified buyers exist. Those four numbers live on the product-market export
          guides, and every sector page links down into them.
        </p>
        <p>
          Nothing on these pages is modelled or forecast. Duty comes from World Bank WITS /
          UNCTAD TRAINS, demand from OEC World / CEPII BACI, HS classification from WCO HS-2022,
          and buyer records from Vametra Buyer Intelligence. Where a source has no record for a
          pair, we say so rather than estimate it.
        </p>
      </AnswerBlock>
      <PageFaq items={INDEX_FAQ} testIdPrefix="industries-faq" />
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

  const cats = (i.exports || []).slice(0, 8).join(", ");
  const mkts = (i.topMarkets || []).slice(0, 8).join(", ");
  const comp = (i.compliance || []).slice(0, 8).join(", ");
  const faqs = [
    {
      q: `What products fall under ${i.name} exports?`,
      a: `${cats || "Export categories are listed on this page"}. Each of these maps to one or more HS chapters, which is what customs authorities actually classify against — so the HS code, not the sector label, decides the duty your buyer pays.`,
    },
    {
      q: `Which countries import the most ${i.name} from India?`,
      a: `${mkts || "The leading markets are listed above"}. Ranking is based on measured import value from OEC World / CEPII BACI rather than opinion, and the market that imports the most is not always the market that pays best once duty and freight are applied.`,
    },
    {
      q: `What compliance does the ${i.name} sector have to clear?`,
      a: `${comp || "Sector compliance requirements are listed on this page"}. These are sector-wide. Destination-specific labelling, certification and documentation vary by market and are set out on the corridor pages and the product-market export guides.`,
    },
    {
      q: `How do I find the import duty for ${i.name} products?`,
      a: `Open the Customs Duty Calculator, enter the 6-digit HS code and pick your origin and destination. You get the applied MFN rate and any preferential rate your origin qualifies for, read from World Bank WITS / UNCTAD TRAINS, with the data year shown next to the number.`,
    },
    {
      q: `Where do I find verified buyers in ${i.name}?`,
      a: `Buyer Intelligence holds contact-verified importer records indexed by HS code and destination market, sourced from official trade records. Coverage is stated per country — where we hold no verified records for a lane, the page says so instead of showing an empty list.`,
    },
  ];

  return (
    <>
      <SEO title={`${i.name} Industry · Exports, Markets, Compliance`}
        description={i.overview}
        path={`/industries/${i.slug}`}
        keywords={`${i.name} industry, ${i.name} export India, ${i.name} compliance, ${i.name} markets`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Industries", path: "/industries" },
          { name: i.name, path: `/industries/${i.slug}` },
        ]}
        faqs={faqs}
      />
      <PageHero testIdPrefix="id" label={`Industry · ${i.name}`} title={i.name} sub={i.overview} />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-2 gap-5">
        <Card title="Export categories"><div className="mt-3"><ChipList items={i.exports} /></div></Card>
        <Card title="Top markets"><div className="mt-3"><ChipList items={i.topMarkets} variant="violet" /></div></Card>
        <Card title="Compliance" className="lg:col-span-2"><div className="mt-3"><ChipList items={i.compliance} /></div></Card>
      </section>
      <AnswerBlock testId="id-answer" label={`${i.name} · how to use this`}
        title={`Turning the ${i.name} sector view into a priced lane`}>
        <p>
          {i.overview}
        </p>
        <p>
          The categories above tell you what the sector ships; the markets tell you where it lands.
          Neither tells you your margin. For that you need the HS6 code of the exact article you
          supply, the applied tariff in the destination, that country's own VAT or GST on imports,
          and your freight — which is what the duty and landed-cost engines compute from live data.
        </p>
        <p>
          A practical order of work: confirm the HS code in the HSN Finder, check applied and
          preferential duty for your origin in the Duty Calculator, size real demand for that HS
          code in Product Research, then build the cost waterfall in the Landed Cost Calculator
          before you approach buyers. Compliance for {i.name} — {comp || "as listed above"} — should
          be cleared in parallel, because certification lead times, not tariffs, are what usually
          delay a first shipment.
        </p>
      </AnswerBlock>
      <PageFaq items={faqs} heading={`${i.name} exports — frequently asked questions`} testIdPrefix="id-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
