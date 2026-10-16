import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { BrainExploreCTA } from "@/components/BrainExplore";
import { loadEntity } from "@/lib/fetchPageData";
import { productSeo } from "@/data/seoTitles";
import { AnswerFirst } from "@/components/AnswerFirst";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { titleize } from "@/lib/slug";
import { api } from "@/lib/api";
import { ArrowRight, TrendUp, Package as PackageIcon, ShieldCheck, Truck } from "@phosphor-icons/react";

const INDEX_FAQ = [
  {
    q: "What is inside a product trade profile?",
    a: "The HSN code the product classifies under, the demand picture for it, the countries that import and export the most of it, the compliance and certifications a shipment has to carry, and the logistics constraints that decide packaging and mode. From there it links into the per-market export guides that carry the applied duty for each destination.",
  },
  {
    q: "Why does the HSN code matter more than the product name?",
    a: "Customs authorities assess duty against the HS code, not the description on your invoice. Two products that sound identical can sit in different HS lines and attract different tariffs and different certification requirements. Every profile states the code so you can verify it before you quote.",
  },
  {
    q: "Where does the demand data come from?",
    a: "Measured world trade values and the top importer and exporter rankings are read from OEC World / CEPII BACI. Applied and preferential tariffs come from World Bank WITS / UNCTAD TRAINS at HS6 level. HS classification follows WCO HS-2022. Each number carries its data year on the page.",
  },
  {
    q: "Which products are covered?",
    a: "The catalogue covers the categories where we hold verified duty and demand data end to end — including basmati rice, Indian spices, agarbatti, cotton textiles, pharmaceuticals, fresh fruits, fresh vegetables and engineering machinery. Each of these has a published export guide for every market that meets our data gate.",
  },
  {
    q: "How do I turn a product profile into a shortlist of markets?",
    a: "Open the product's export guide hub. It ranks every published market for that product by applied duty and measured import demand, so you can shortlist three or four destinations, then cost each one properly in the Landed Cost Calculator before you contact buyers.",
  },
];

export function ProductsIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/products-catalog").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO title="Export Products from India: HS Code, Duty, Buyers | Vametra"
        description="Premium product trade profiles — global demand, top markets, compliance and opportunities for India's biggest export categories, each linked to per-market export guides with applied import duty."
        path="/products"
        keywords="export product list, basmati rice export, spices export, agarbatti export, pharmaceuticals export, textiles export"
        breadcrumbs={[{ name: "Home", path: "/" }, { name: "Products", path: "/products" }]}
        faqs={INDEX_FAQ}
      />
      <PageHero testIdPrefix="products" label="Product Trade Profiles"
        title="Export products from India — HS code, duty and buyers per product."
        sub="Demand, top buyers, compliance and trade opportunities — for every product, in one page."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {list.map((p) => (
            <Link key={p.slug} to={`/products/${p.slug}`} data-testid={`products-card-${p.slug}`}
              className="group glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
              <div className="h-44 relative overflow-hidden">
                <img src={p.image} alt={p.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                <div className="absolute top-3 left-3 glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{p.category}</div>
              </div>
              <div className="p-5">
                <h3 className="font-display font-bold text-lg">{p.name}</h3>
                <div className="text-xs text-slate-400 mt-1">HSN {p.hsn}</div>
                <div className="mt-4 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                  Open profile <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <AnswerBlock testId="products-answer" label="Method"
        title="Why we publish by product and market, not by product alone">
        <p>
          A product's global demand tells you almost nothing about whether a specific shipment
          earns money. The same article can face a zero tariff in one market and a double-digit
          tariff in the next, and the destination's VAT or GST on imports often matters more than
          the duty itself.
        </p>
        <p>
          So every profile here is a starting point into a per-market guide. The profile fixes the
          HS code, the compliance set and the logistics reality. The guide then fixes the numbers
          for one destination: applied MFN rate, any preferential rate your origin qualifies for,
          measured import demand for that HS code, and whether we hold verified buyer records.
        </p>
        <p>
          Every figure carries its source and data year. Where World Bank WITS has no record for a
          country-product pair, or where we hold no verified buyers for a lane, the page states that
          plainly instead of substituting an estimate.
        </p>
      </AnswerBlock>
      <BrainExploreCTA kind="product" testIdPrefix="products-explore" />
      <PageFaq items={INDEX_FAQ} testIdPrefix="products-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

const SEO_PRODUCT_SLUG = {
  "basmati-rice": "basmati-rice", agarbatti: "agarbatti", spices: "indian-spices",
  textiles: "cotton-textiles", pharmaceuticals: "pharmaceuticals",
};

export default function ProductDetail() {
  const { slug } = useParams();
  const [p, setP] = useState(null);
  const [nf, setNf] = useState(false);
  const [hub, setHub] = useState(null);
  useEffect(() => {
    setP(null); setNf(false); setHub(null);
    loadEntity(`/product/${slug}`, setP, () => setNf(true));
    const seoSlug = SEO_PRODUCT_SLUG[String(slug || "").toLowerCase()];
    if (seoSlug) api.get(`/seo/product-hub/${seoSlug}`, { timeout: 120000 }).then((r) => setHub(r.data)).catch(() => {});
  }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><SEO title="Not found" description="This page does not exist." noindex /><h1 className="font-display font-extrabold text-4xl">Product not found</h1><Link to="/products" className="btn-primary mt-6 inline-flex">Browse products</Link></div>;
  if (!p) {
    const n = titleize(slug);
    return (
      <div className="max-w-7xl mx-auto px-6 py-32">
        <SEO title={productSeo(n).title}
          description={`${n} export profile: HSN code, demand, leading markets, compliance and certifications, with applied import duty per destination — Vametra AI.`}
          path={`/products/${slug}`}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "Products", path: "/products" }, { name: n, path: `/products/${slug}` }]} />
        <h1 className="font-display font-extrabold text-4xl">{productSeo(n).h1}</h1>
        <p className="text-slate-400 mt-4 text-sm">Loading…</p>
      </div>
    );
  }

  const faqs = [
    { q: `What is the HSN code for exporting ${p.name}?`, a: `${p.name} falls under category ${p.category} and classifies under HSN ${p.hsn}. Customs assesses duty against the HS code rather than the product description, so confirm the exact line in the HSN Finder before you quote — GST, RoDTEP and drawback all follow the code.` },
    { q: `Which countries are the best export markets for ${p.name}?`, a: `${String(p.overview || "").substring(0, 200)}` },
    { q: `What does it cost my buyer to import ${p.name}?`, a: `That depends on the destination's applied tariff for HSN ${p.hsn}, its own VAT or GST on imports, and your freight terms. The Landed Cost Calculator builds the full Ex-Works to landed waterfall using live World Bank WITS duty and exchange rates, so you can see what your buyer actually pays in each market.` },
    { q: `What compliance and certification does ${p.name} need?`, a: `${(p.compliance || []).slice(0, 6).join(", ") || "Compliance requirements are listed on this page"}${(p.certifications || []).length ? `, plus certifications including ${(p.certifications || []).slice(0, 5).join(", ")}` : ""}. Certification lead time, not tariffs, is usually what delays a first shipment.` },
    { q: `How do I find verified buyers for ${p.name}?`, a: `Use Vametra AI's Verified Buyer Intelligence to reach contact-verified importers of ${p.name} sourced from official government trade records across 32 countries. Coverage is stated per market, and where we hold no verified records for a lane the page says so.` },
  ];

  return (
    <>
      <SEO title={productSeo(p.name).title}
        description={`${p.name} export from India: HSN ${p.hsn}, ${p.overview.substring(0, 110)}`}
        path={`/products/${p.slug}`}
        keywords={`${p.name} export, ${p.name} HSN, ${p.name} compliance, ${p.name} buyers, export ${p.name} from India`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Products", path: "/products" },
          { name: p.name, path: `/products/${p.slug}` },
        ]}
        faqs={faqs}
        schema={{ "@context": "https://schema.org", "@type": "Thing", name: p.name, description: p.overview, additionalType: "https://schema.org/ProductGroup" }}
      />
      <section className="relative pt-16 pb-10">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-7">
            <SectionLabel>Product Trade Profile · HSN {p.hsn}</SectionLabel>
            <h1 data-testid="pd-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl mt-4">{productSeo(p.name).h1}</h1>
            <p className="mt-5 text-slate-300 text-lg max-w-2xl">{p.overview}</p>
            <div className="mt-6 flex flex-wrap gap-2 text-xs">
              <Link to={`/hsn/${p.hsn}`} className="glass px-3 py-1.5 rounded-full hover:border-cyan-400/30">HSN {p.hsn}</Link>
              <span className="glass px-3 py-1.5 rounded-full">{p.category}</span>
            </div>
          </div>
          <div className="lg:col-span-5">
            <div className="rounded-3xl overflow-hidden border border-white/10 h-[260px] relative">
              <img src={p.image} alt={p.name} className="absolute inset-0 w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-transparent to-transparent" />
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-3 gap-5">
        <Card title="Demand" Icon={TrendUp} className="lg:col-span-1"><div className="mt-3 text-slate-300">{p.demand}</div></Card>
        <Card title="Top Importers" className="lg:col-span-1"><div className="mt-3"><ChipList items={p.topImporters} variant="cyan" /></div></Card>
        <Card title="Top Exporters" className="lg:col-span-1"><div className="mt-3"><ChipList items={p.topExporters} variant="violet" /></div></Card>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-5 grid lg:grid-cols-2 gap-5">
        <Card title="Trade Opportunities" Icon={PackageIcon}>
          <ul className="mt-3 space-y-2 text-sm">{p.opportunities.map((o, i) => <li key={i} className="flex gap-2"><ArrowRight size={14} className="text-cyan-300 mt-1" />{o}</li>)}</ul>
        </Card>
        <Card title="Compliance" Icon={ShieldCheck}>
          <div className="mt-3"><ChipList items={p.compliance} variant="violet" /></div>
          <div className="mt-4 text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Certifications</div>
          <div className="mt-2"><ChipList items={p.certifications} /></div>
        </Card>
        <Card title="Logistics" Icon={Truck} className="lg:col-span-2"><div className="mt-3 text-slate-300">{p.logistics}</div></Card>
      </section>

      {p.relatedCorridors?.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-10">
          <h2 className="font-display font-bold text-2xl">Related trade corridors</h2>
          <div className="mt-4 grid sm:grid-cols-2 gap-4">
            {p.relatedCorridors.map((c) => (
              <Link key={c} to={`/corridors/${c}`} className="glass rounded-2xl px-5 py-4 flex items-center justify-between hover:border-cyan-400/30">
                <span className="text-sm capitalize">{c.replace(/-/g, " ")}</span>
                <ArrowRight size={14} className="text-cyan-300" />
              </Link>
            ))}
          </div>
        </section>
      )}

      {hub?.markets?.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-10" data-testid="pd-markets">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display font-bold text-2xl">Export guides by market</h2>
              <p className="text-sm text-slate-400 mt-1.5">
                {hub.stats.markets} published markets with real duty and demand data · duty {hub.stats.dutyMin}–{hub.stats.dutyMax}%
              </p>
            </div>
            <Link to={hub.url} data-testid="pd-hub-link" className="btn-ghost text-sm">
              Open {hub.name} hub <ArrowRight size={13} />
            </Link>
          </div>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {hub.markets.slice(0, 24).map((m) => (
              <Link key={m.url} to={m.url} data-testid={`pd-market-${m.countrySlug}`}
                className="text-[12px] glass rounded-full px-3 py-1.5 hover:border-cyan-400/40 transition-colors">
                {m.country} <span className="text-slate-500">{m.dutyRate != null ? `${m.dutyRate}%` : ""}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <AnswerBlock testId="pd-answer" label={`${p.name} · how to use this profile`}
        title={`What decides whether ${p.name} is worth exporting to a given market`}>
        <p>
          Four numbers, in this order. First the HS code — {p.name} classifies under HSN {p.hsn},
          and that code, not the description on your invoice, is what the destination's customs
          authority assesses. Second the applied tariff in that destination for that code, plus any
          preferential rate your origin qualifies for under a trade agreement.
        </p>
        <p>
          Third, the destination's own import tax stack — VAT or GST is frequently larger than the
          duty and is charged on the duty-inclusive value, so it compounds. Fourth, real demand:
          whether that market actually imports meaningful volume of this HS code, read from measured
          trade data rather than inferred from population or GDP.
        </p>
        <p>
          {p.logistics ? `${p.logistics} ` : ""}Only after those four is buyer outreach worth your
          time — which is why the market links on this page lead to guides that state all four for
          a single destination, with the source and data year attached to every figure.
        </p>
      </AnswerBlock>
      <AnswerFirst testId="pd-answer-first" eyebrow={`${p.name} · direct answer`}
        answer={`${p.name} export from India starts with HSN ${p.hsn}. ${p.overview} The applied import duty per destination comes from World Bank WITS, demand from OEC/BACI, and verified buyers from official registries — each market we publish links to its own export guide below.`}
        rows={[
          { label: "HSN", value: String(p.hsn) },
          { label: "Duty source", value: "WITS / TRAINS · HS6" },
          { label: "Demand source", value: "OEC World (BACI)" },
          { label: "Verified buyer countries", value: "{buyerCountries}" },
        ]}
        source="WCO HS-2022; World Bank WITS / UNCTAD TRAINS; OEC World (BACI); official registries"
        links={[
          { to: `/tools/duty-calculator?hs=${String(p.hsn).replace(/\D/g, "").slice(0, 6)}`, label: `Duty for ${p.name}` },
          { to: `/tools/find-buyers`, label: `Buyers for ${p.name}` },
          { to: "/export", label: "Export guides" },
          { to: "/products", label: "All export products" },
          { to: "/corridors/india-to-uae", label: "India → UAE corridor" },
        ]} />
      <BrainExploreCTA kind="product" defaults={{ product: p.name, hs: String(p.hsn || "").replace(/\D/g, "").slice(0, 6) }} testIdPrefix="pd-explore" title={`${p.name} into a market we have not published, or a different product entirely? Ask the Brain.`} />
      <PageFaq items={faqs} heading={`Exporting ${p.name} — frequently asked questions`} testIdPrefix="pd-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
