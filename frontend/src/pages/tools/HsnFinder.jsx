import React, { useState } from "react";
import { ToolShell, CTARow, Card, ChipList } from "@/components/ToolShell";
import SEO from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { api } from "@/lib/api";
import { MagnifyingGlass } from "@phosphor-icons/react";

const CATEGORIES = ["Agriculture & Food", "FMCG", "Textiles & Apparel", "Pharmaceuticals", "Engineering", "Chemicals", "Handicrafts"];

export default function HsnFinder() {
  const [form, setForm] = useState({ productName: "Basmati Rice", description: "long grain aromatic rice", category: "Agriculture & Food" });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/hsn-finder", form);
      setResults(data.results || []);
    } finally { setLoading(false); }
  };

  React.useEffect(() => { submit(); /* initial */ }, []); // eslint-disable-line

  return (
    <>
      <SEO
        title="HSN Code Finder · Free GST + RoDTEP Lookup"
        description="Find the correct HSN code, GST rate, RoDTEP eligibility and export compliance for any product. Free, instant, India-first."
        path="/tools/hsn-finder"
        keywords="HSN finder India, HSN code search, GST rate by product, RoDTEP eligibility, HS code lookup"
      />
      <ToolShell testIdPrefix="hsn"
        label="HSN Finder"
        title="Find your HSN code in seconds."
        sub="Paste a product name, add a quick description and pick a category. We'll return the most likely HSN codes with GST, RoDTEP and compliance attached."
      >
        <div className="grid lg:grid-cols-12 gap-8">
          <form onSubmit={submit} className="lg:col-span-5 glass-strong rounded-3xl p-6 sm:p-7 space-y-4">
            <Field label="Product name">
              <input data-testid="hsn-product" value={form.productName} onChange={(e) => setForm({ ...form, productName: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" />
            </Field>
            <Field label="Description (optional)">
              <textarea data-testid="hsn-description" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none" />
            </Field>
            <Field label="Category">
              <select data-testid="hsn-category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none">
                {CATEGORIES.map((c) => <option key={c} className="bg-[#0a0f24]">{c}</option>)}
              </select>
            </Field>
            <button data-testid="hsn-submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading ? "Searching…" : <><MagnifyingGlass size={16} weight="bold" /> Find HSN code</>}
            </button>
            <CTARow testIdPrefix="hsn-cta" />
          </form>

          <div className="lg:col-span-7 space-y-4">
            {results.map((r, i) => (
              <div key={r.code} data-testid={`hsn-result-${i}`} className="glass-strong rounded-3xl p-6">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">HSN · {r.code}</div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-400 font-mono-display">Match · {r.matchScore}</div>
                </div>
                <h2 className="font-display font-bold text-2xl mt-2">{r.title}</h2>
                <div className="mt-5 grid sm:grid-cols-3 gap-3">
                  <Mini label="GST" value={r.gst} />
                  <Mini label="RoDTEP" value={r.rodtep} />
                  <Mini label="Drawback" value={r.drawback} />
                </div>
                <Card title="Export benefits" className="mt-4 !p-4">
                  <div className="mt-3"><ChipList items={r.exportBenefits} testIdPrefix={`hsn-${i}-benefit`} /></div>
                </Card>
                <Card title="Documents" className="mt-3 !p-4">
                  <div className="mt-3"><ChipList items={r.documents} variant="violet" testIdPrefix={`hsn-${i}-doc`} /></div>
                </Card>
                <div className="mt-4 text-sm text-slate-400">📍 {r.customsNotes}</div>
              </div>
            ))}
          </div>
        </div>
      </ToolShell>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}

function Field({ label, children }) {
  return <label className="block"><div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>{children}</label>;
}
function Mini({ label, value }) {
  return <div className="glass rounded-2xl p-3"><div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div><div className="mt-1 font-display font-bold text-sm">{value}</div></div>;
}
