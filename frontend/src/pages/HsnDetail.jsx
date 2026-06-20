import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { ArrowRight } from "@phosphor-icons/react";

export default function HsnDetail() {
  const { code } = useParams();
  const [h, setH] = useState(null);
  const [nf, setNf] = useState(false);
  useEffect(() => {
    setH(null); setNf(false);
    api.get(`/hsn/${code}`).then((r) => r.data?.error ? setNf(true) : setH(r.data)).catch(() => setNf(true));
  }, [code]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">HSN {code} not found</h1><Link to="/tools/hsn-finder" className="btn-primary mt-6 inline-flex">Try HSN Finder</Link></div>;
  if (!h) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={`HSN ${h.code} — ${h.title} · GST, RoDTEP & Compliance`}
        description={`HSN ${h.code} (${h.title}) — GST ${h.gst}, RoDTEP ${h.rodtep}, drawback ${h.drawback}. Export benefits, documents and compliance.`}
        path={`/hsn/${h.code}`}
        keywords={`HSN ${h.code}, ${h.title} HSN, GST rate ${h.code}, RoDTEP ${h.code}, ${h.title} export`}
      />
      <PageHero testIdPrefix="hsn-detail" label={`HSN · ${h.code}`}
        title={h.title}
        sub={`Category: ${h.category}. ${h.opportunities}`}
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid sm:grid-cols-3 gap-4">
        <Mini label="GST" value={h.gst} />
        <Mini label="RoDTEP" value={h.rodtep} />
        <Mini label="Duty Drawback" value={h.drawback} />
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-6 grid lg:grid-cols-2 gap-5">
        <Card title="Export Benefits"><div className="mt-3"><ChipList items={h.exportBenefits} /></div></Card>
        <Card title="Documents Required"><div className="mt-3"><ChipList items={h.documents} variant="violet" /></div></Card>
        <Card title="Customs Notes" className="lg:col-span-2"><p className="mt-3 text-slate-300 text-sm">{h.customsNotes}</p></Card>
      </section>

      {h.relatedProducts?.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-8">
          <h2 className="font-display font-bold text-2xl">Related products</h2>
          <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {h.relatedProducts.map((p) => (
              <Link key={p} to={`/products/${p}`} className="glass rounded-2xl px-4 py-3 capitalize flex items-center justify-between hover:border-cyan-400/30">
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
function Mini({ label, value }) {
  return <div className="glass rounded-2xl p-5"><div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div><div className="mt-2 font-display font-bold text-xl">{value}</div></div>;
}
