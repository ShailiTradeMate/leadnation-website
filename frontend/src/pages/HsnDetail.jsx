import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card, ChipList } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { loadEntity } from "@/lib/fetchPageData";
import { AnswerBlock, PageFaq } from "@/components/PageFaq";
import { ArrowRight } from "@phosphor-icons/react";

export default function HsnDetail() {
  const { code } = useParams();
  const [h, setH] = useState(null);
  const [nf, setNf] = useState(false);
  useEffect(() => {
    setH(null); setNf(false);
    loadEntity(`/hsn/${code}`, setH, () => setNf(true));
  }, [code]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><SEO title="Not found" description="This page does not exist." noindex /><h1 className="font-display font-extrabold text-4xl">HSN {code} not found</h1><Link to="/tools/hsn-finder" className="btn-primary mt-6 inline-flex">Try HSN Finder</Link></div>;
  if (!h) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32">
        <SEO title={`HSN ${code} · GST, RoDTEP & Export Compliance`}
          description={`HSN ${code}: GST rate, RoDTEP and duty drawback, export benefits, required documents and customs notes, plus applied import duty per destination — Vametra AI.`}
          path={`/hsn/${code}`}
          breadcrumbs={[{ name: "Home", path: "/" }, { name: "HSN Codes", path: "/tools/hsn-finder" }, { name: `HSN ${code}`, path: `/hsn/${code}` }]} />
        <h1 className="font-display font-extrabold text-4xl">HSN {code}</h1>
        <p className="text-slate-400 mt-4 text-sm">Loading…</p>
      </div>
    );
  }

  const faqs = [
    {
      q: `What is the GST rate for HSN ${h.code}?`,
      a: `HSN ${h.code} (${h.title}) attracts GST of ${h.gst}. For exports, GST is generally zero-rated against a LUT or refundable, but the rate still governs your domestic procurement and your refund claim, so it matters to working capital even when nothing is payable on the shipment itself.`,
    },
    {
      q: `What export benefits apply to HSN ${h.code}?`,
      a: `RoDTEP is ${h.rodtep} and duty drawback is ${h.drawback} for this line. These are published rates against the HS code — they are claimed, not granted automatically, and the claim depends on the shipping bill being filed with the correct scheme declaration at the time of export.`,
    },
    {
      q: `What documents are required to export HSN ${h.code}?`,
      a: `${(h.documents || []).slice(0, 8).join(", ") || "Standard export documentation applies"}. The country-specific additions — certificates of origin, health or phytosanitary certificates, conformity marks — depend on the destination, which is why the full checklist sits on the per-market export guides.`,
    },
    {
      q: `How much import duty will my buyer pay on HSN ${h.code}?`,
      a: `That is set by the destination, not by India. Enter HS ${h.hs6 || h.code} in the Customs Duty Calculator with your origin and the buyer's country and you get the applied MFN rate plus any preferential rate your origin qualifies for, read from World Bank WITS / UNCTAD TRAINS with the data year shown.`,
    },
    {
      q: `Which countries import the most under HSN ${h.code}?`,
      a: `Run the code through Product Research for the measured world trade value, the ranked importing and exporting countries and the multi-year trend from OEC World / CEPII BACI. Demand ranking is independent of duty, so always read the two together before shortlisting a market.`,
    },
    {
      q: `Is a 6-digit HS code enough to clear customs?`,
      a: `For duty research, yes — HS6 is the internationally harmonised level and is what tariff databases publish. For the actual declaration you will need the destination's full national tariff line, which extends to 8 or 10 digits and is country-specific.`,
    },
  ];

  return (
    <>
      <SEO title={`HSN ${h.code} — ${h.title} · GST, RoDTEP & Compliance`}
        description={`HSN ${h.code} (${h.title}) — GST ${h.gst}, RoDTEP ${h.rodtep}, drawback ${h.drawback}. Export benefits, documents and compliance.`}
        path={`/hsn/${h.code}`}
        keywords={`HSN ${h.code}, ${h.title} HSN, GST rate ${h.code}, RoDTEP ${h.code}, ${h.title} export`}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "HSN Codes", path: "/tools/hsn-finder" },
          { name: `HSN ${h.code}`, path: `/hsn/${h.code}` },
        ]}
        faqs={faqs}
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

      <section className="max-w-7xl mx-auto px-6 sm:px-10 mt-5 flex flex-wrap gap-2" data-testid="hsn-detail-tools">
        <Link to={`/tools/duty-calculator?hs=${h.hs6 || h.code}&from=356&to=784`} className="btn-primary !py-2 text-sm">Import duty for HS {h.hs6 || h.code}</Link>
        <Link to={`/tools/product-research?hs=${h.hs6 || h.code}`} className="btn-ghost !py-2 text-sm">Who imports it (real data)</Link>
        <Link to={`/tools/landed-cost-calculator?hs=${h.hs6 || h.code}&from=356&to=784`} className="btn-ghost !py-2 text-sm">Cost a shipment</Link>
        <Link to={`/buyers?hs=${h.hs6 || h.code}`} className="btn-ghost !py-2 text-sm">Find buyers</Link>
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

      <AnswerBlock testId="hsn-detail-answer" label={`HSN ${h.code} · how to use this`}
        title={`What HSN ${h.code} decides for your shipment`}>
        <p>
          {h.customsNotes || `HSN ${h.code} covers ${h.title}.`} The code is the single most
          consequential field on your paperwork: it sets the GST treatment at home, the export
          incentive rates you can claim, and — in the destination — the applied tariff, the
          preferential rate you may qualify for and the certification regime at the border.
        </p>
        <p>
          Domestically this line carries GST of {h.gst}, RoDTEP of {h.rodtep} and duty drawback of{" "}
          {h.drawback}. Those are published rates against the code, but they are claimed rather
          than granted — the scheme has to be declared correctly on the shipping bill at the time
          of export, and a misdeclaration is not retrospectively fixable.
        </p>
        <p>
          {h.opportunities || ""} On the destination side nothing is fixed until you name a country,
          so the practical sequence is: confirm this code is right for your exact article, run it
          through the Duty Calculator for each candidate market, size real demand in Product
          Research, then cost a shipment properly before you quote.
        </p>
      </AnswerBlock>
      <PageFaq items={faqs} heading={`HSN ${h.code} — frequently asked questions`} testIdPrefix="hsn-detail-faq" />
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}
function Mini({ label, value }) {
  return <div className="glass rounded-2xl p-5"><div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div><div className="mt-2 font-display font-bold text-xl">{value}</div></div>;
}
