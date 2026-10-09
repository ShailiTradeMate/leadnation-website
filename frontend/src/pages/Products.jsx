import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight, TrendUp, Package as PackageIcon, ShieldCheck, Truck } from "@phosphor-icons/react";

export function ProductsIndex() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/products-catalog").then((r) => setList(r.data)); }, []);

  return (
    <>
      <SEO title="Product Trade Profiles · Basmati, Spices, Pharma & More"
        description="Premium product trade profiles — global demand, top markets, compliance and opportunities for India's biggest export categories."
        path="/products"
        keywords="export product list, basmati rice export, spices export, agarbatti export, pharmaceuticals export, textiles export"
      />
      <PageHero testIdPrefix="products" label="Product Trade Profiles"
        title="Pick a product. See the global playbook."
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
    api.get(`/product/${slug}`).then((r) => r.data?.error ? setNf(true) : setP(r.data)).catch(() => setNf(true));
    const seoSlug = SEO_PRODUCT_SLUG[String(slug || "").toLowerCase()];
    if (seoSlug) api.get(`/seo/product-hub/${seoSlug}`, { timeout: 120000 }).then((r) => setHub(r.data)).catch(() => {});
  }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">Product not found</h1><Link to="/products" className="btn-primary mt-6 inline-flex">Browse products</Link></div>;
  if (!p) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={`${p.name} — Export Guide, HSN, Compliance & Markets`}
        description={`${p.overview.substring(0, 160)}`}
        path={`/products/${p.slug}`}
        keywords={`${p.name} export, ${p.name} HSN, ${p.name} compliance, ${p.name} buyers, export ${p.name} from India`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Products", path: "/products" },
          { name: p.name, path: `/products/${p.slug}` },
        ]}
        faqs={[
          { q: `What is the HSN code for exporting ${p.name}?`, a: `${p.name} falls under category ${p.category}. Vametra AI lists the exact HSN code, GST, RoDTEP and drawback for ${p.name}.` },
          { q: `Which countries are the best export markets for ${p.name}?`, a: `${p.overview.substring(0, 200)}` },
          { q: `How do I find verified buyers for ${p.name}?`, a: `Use Vametra AI's Verified Buyer Intelligence to reach contact-verified importers of ${p.name} sourced from official government trade records across 195+ countries.` },
        ]}
        schema={{ "@context": "https://schema.org", "@type": "Product", name: p.name, category: p.category, description: p.overview }}
      />
      <section className="relative pt-16 pb-10">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-7">
            <SectionLabel>Product Trade Profile · HSN {p.hsn}</SectionLabel>
            <h1 data-testid="pd-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-6xl mt-4">{p.name}</h1>
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

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
