import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import SEO from "@/components/SEO";
import { RelatedGuides } from "@/components/LinkGraph";
import { api } from "@/lib/api";
import {
  ArrowRight, Scales, Globe, FileText, Users, Calculator,
  CalendarBlank, Newspaper, Brain, SealCheck, Truck,
} from "@phosphor-icons/react";

const money = (v) => {
  if (v == null) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v}`;
};
const pct = (v) => (v == null ? "—" : `${v}%`);

const Section = ({ icon: Icon, title, kicker, children, testId }) => (
  <section data-testid={testId} className="scroll-mt-24">
    <div className="flex items-center gap-2.5 mb-4">
      {Icon && <Icon size={17} weight="duotone" className="text-cyan-300" />}
      <h2 className="font-display font-bold text-xl sm:text-2xl">{title}</h2>
    </div>
    {kicker && <p className="text-sm text-slate-400 mb-4 max-w-3xl">{kicker}</p>}
    {children}
  </section>
);

const Fact = ({ label, value, sub }) => (
  <div className="glass rounded-2xl p-4">
    <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400">{label}</div>
    <div className="font-display font-extrabold text-2xl mt-1.5">{value}</div>
    {sub && <div className="text-[11px] text-slate-400 mt-1">{sub}</div>}
  </div>
);

const ToolLink = ({ to, label, note, icon: Icon, testId }) => (
  <Link
    to={to}
    data-testid={testId}
    className="glass rounded-2xl p-4 flex items-start gap-3 hover:border-cyan-400/40 border border-transparent transition-colors group"
  >
    <Icon size={18} weight="duotone" className="text-cyan-300 mt-0.5 shrink-0" />
    <span className="min-w-0">
      <span className="block text-sm font-semibold">{label}</span>
      <span className="block text-[11px] text-slate-400 leading-snug">{note}</span>
    </span>
    <ArrowRight size={14} className="ml-auto mt-1 text-slate-500 group-hover:text-cyan-300 shrink-0" />
  </Link>
);

export default function ExportProductCountry() {
  const { product, country } = useParams();
  const [d, setD] = useState(null);
  const [state, setState] = useState("loading");

  useEffect(() => {
    let dead = false;
    setState("loading");
    api.get(`/seo/page-data/${product}/${country}`)
      .then(({ data }) => { if (!dead) { setD(data); setState("ready"); } })
      .catch(() => { if (!dead) setState("error"); });
    return () => { dead = true; };
  }, [product, country]);

  if (state === "loading") {
    return <div data-testid="epc-loading" className="max-w-7xl mx-auto px-5 sm:px-10 py-28 text-slate-400">Loading live trade data…</div>;
  }
  if (state === "error" || !d?.ok) {
    return (
      <div data-testid="epc-error" className="max-w-3xl mx-auto px-5 py-28">
        <SEO title="Export guide not found" description="This export guide is not available." path={`/export/${product}/to/${country}`} noindex />
        <h1 className="font-display font-extrabold text-3xl">We don't publish this combination yet</h1>
        <p className="text-slate-400 mt-3 text-sm">
          We only publish a product-market guide when we hold real tariff and trade data for it.
          Try the <Link to="/tools/duty-calculator" className="text-cyan-300 underline">duty calculator</Link> or
          ask the <Link to="/brain" className="text-cyan-300 underline">Vametra AI Brain</Link> directly.
        </p>
      </div>
    );
  }

  const { product: p, country: c, duty, demand, buyers, expos, news } = d;
  const imp = duty?.importDuty;
  const pref = duty?.preferential;
  const benefit = duty?.exportBenefit;
  const effective = pref?.rate != null ? pref.rate : imp?.rate;

  // Answer-first paragraph — the 40-60 words AI engines quote.
  const answer = `${p.name} exported from India to ${c.name} is classified under HS ${duty?.hsCode || p.primaryHs}` +
    (imp ? ` and attracts a ${pct(imp.rate)} ${imp.type} import duty in ${c.name} (${imp.source}, ${imp.year})` : "") +
    (pref ? `, reduced to ${pct(pref.rate)} under ${pref.type}` : "") +
    (benefit ? `. Indian exporters can claim ${benefit.rate}% of FOB under ${benefit.scheme}` : "") +
    (demand?.countryImportsUSD ? `. ${c.name} imported ${money(demand.countryImportsUSD)} of this product in ${demand.year}, ranking #${demand.countryRank} worldwide` : "") + ".";

  const faqs = [
    { q: `Can I export ${p.name} from India to ${c.name}?`,
      a: `Yes. ${p.name} is traded under HS ${duty?.hsCode || p.primaryHs}. ${imp ? `${c.name} applies a ${pct(imp.rate)} ${imp.type} duty (${imp.year}).` : ""} You will need the standard Indian export documentation set plus any product-specific certification required by ${c.name}.` },
    { q: `What is the HS code for ${p.name}?`,
      a: `${p.name} falls under HS ${p.primaryHs}${p.hs.length > 1 ? ` (related codes: ${p.hs.join(", ")})` : ""}. Confirm the exact 8-digit national code with our HS code finder before filing the shipping bill.` },
    { q: `How much import duty does ${c.name} charge on ${p.name}?`,
      a: imp ? `${pct(imp.rate)} — ${imp.type}, as reported to ${imp.source} for ${imp.year}.${pref ? ` A preferential rate of ${pct(pref.rate)} applies under ${pref.type}.` : ""} Verify against the current ${c.name} customs tariff before contracting.` : `We do not hold a verified tariff record for this combination yet. Use the duty calculator for an estimate and confirm with ${c.name} customs.` },
    { q: `What export incentive can I claim from India?`,
      a: benefit ? `${benefit.scheme} at ${benefit.rate}% of FOB value (${benefit.source}, effective ${benefit.effectiveDate}). It is issued as a transferable e-scrip. Confirm the exact 8-digit rate in Appendix 4R.` : `No RoDTEP rate is mapped for this HS code yet — check the DGFT Appendix 4R schedule or run the export incentive finder.` },
    { q: `How big is the ${c.name} market for ${p.name}?`,
      a: demand?.countryImportsUSD ? `${c.name} imported ${money(demand.countryImportsUSD)} in ${demand.year} — ${demand.countryShare}% of world imports and rank #${demand.countryRank} of ${demand.countriesReporting} importing countries (${demand.source}).` : `World imports were ${money(demand?.worldImportsUSD)} in ${demand?.year || "the latest year"}; a country-level figure for ${c.name} is not separately reported.` },
    { q: `Which documents do I need?`,
      a: `Commercial invoice, packing list, shipping bill, bill of lading or airway bill and certificate of origin are the baseline. Preferential duty requires a valid origin certificate. Food, pharma and plant products additionally need phytosanitary, health or regulatory certificates for ${c.name}.` },
    { q: `Are there verified buyers for ${p.name} in ${c.name}?`,
      a: buyers?.covered ? `Yes — Vametra currently holds ${buyers.total.toLocaleString()} screened buyer records in ${c.name}, of which ${buyers.matchingHs} match this HS family and ${buyers.matchingSector} operate in ${p.sector}.` : `Buyer coverage for ${c.name} is still being ingested. Every record is sanctions-screened before publication, so we would rather show nothing than show an unverified list.` },
    { q: `What will the landed cost be?`,
      a: `Landed cost = FOB + freight + insurance + ${effective != null ? `${pct(effective)} duty` : "destination duty"} + local taxes and handling. Run the landed cost calculator for a worked figure in your own currency and Incoterm.` },
  ];

  const title = `Export ${p.name} from India to ${c.name} — Duty, HS Code & Buyers`;
  const description = (imp
    ? `${c.name} import duty on ${p.name} is ${pct(imp.rate)} (${imp.year}). HS ${duty?.hsCode}. `
    : `${p.name} export guide for ${c.name}. HS ${p.primaryHs}. `) +
    (demand?.countryImportsUSD ? `Market size ${money(demand.countryImportsUSD)} (${demand.year}). ` : "") +
    `Documents, incentives, buyers and landed cost — Vametra AI.`;

  return (
    <div data-testid="export-product-country-page">
      <SEO
        title={title}
        description={description}
        path={d.url}
        type="article"
        noindex={!d.indexable}
        faqs={faqs}
        breadcrumbs={[
          { name: "Home", path: "/" },
          { name: "Products", path: "/products" },
          { name: p.name, path: `/products/${p.slug}` },
          { name: `To ${c.name}`, path: d.url },
        ]}
        schema={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          name: title,
          description,
          dateModified: d.generatedAt,
          about: { "@type": "Product", name: p.name, category: p.sector },
          isPartOf: { "@type": "WebSite", name: "Vametra AI", url: "https://vametra.com" },
        }}
      />

      <div className="max-w-7xl mx-auto px-5 sm:px-10 pt-16 sm:pt-20 pb-20">
        <div className="reveal-up">
          <nav aria-label="Breadcrumb" className="text-[11px] font-mono-display tracking-[0.18em] uppercase text-slate-500">
            <Link to="/products" className="hover:text-cyan-300">Products</Link> ·{" "}
            <Link to={`/export/${p.slug}`} className="hover:text-cyan-300" data-testid="epc-hub-crumb">{p.name}</Link> ·{" "}
            {["europe", "middle-east", "asia-pacific"].includes(c.region) && (
              <><Link to={`/regions/${c.region}`} data-testid="epc-region-link" className="hover:text-cyan-300">{c.region.replace("-", " ")}</Link> · </>
            )}
            {c.name}
          </nav>
          <h1 data-testid="epc-h1" className="font-display font-extrabold tracking-tight text-3xl sm:text-4xl lg:text-5xl mt-4 leading-[1.08]">
            Export {p.name} from India to{" "}
            <span className="gradient-text">{c.name}</span>
          </h1>

          {/* Answer-first block */}
          <p data-testid="epc-answer" className="mt-5 text-[15px] sm:text-base text-slate-200 max-w-3xl leading-relaxed">
            {answer}
          </p>
          {!d.indexable && (
            <div data-testid="epc-thin-notice" className="mt-4 text-[11px] font-mono-display tracking-wider uppercase text-amber-300/80">
              Partial data · this guide is excluded from search indexing until verified figures are complete
            </div>
          )}
        </div>

        {/* Trade snapshot */}
        <div className="reveal-up">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-8" data-testid="epc-snapshot">
            <Fact label="HS Code" value={duty?.hsCode || p.primaryHs} sub={p.sector} />
            <Fact label={`${c.name} import duty`} value={pct(imp?.rate)} sub={imp ? `${imp.type} · ${imp.year}` : "no verified record"} />
            <Fact label="India export benefit" value={benefit ? `${benefit.rate}%` : "—"} sub={benefit ? `${benefit.scheme} of FOB` : "not mapped"} />
            <Fact label={`${c.name} imports`} value={money(demand?.countryImportsUSD)} sub={demand?.countryRank ? `rank #${demand.countryRank} of ${demand.countriesReporting} · ${demand.year}` : demand?.year ? `world ${money(demand.worldImportsUSD)} · ${demand.year}` : "—"} />
          </div>
        </div>

        <div className="mt-14 grid lg:grid-cols-12 gap-10">
          <div className="lg:col-span-8 space-y-14">
            {/* Duty table */}
            <Section icon={Scales} title={`Duty & taxes in ${c.name}`} testId="epc-duty"
              kicker="Officially reported applied rates. Always confirm against the destination customs tariff before you contract.">
              <div className="glass-strong rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-white/5">
                    <tr><td className="px-4 py-3 text-slate-400">MFN applied duty</td><td className="px-4 py-3 text-right font-semibold">{pct(imp?.rate)}</td></tr>
                    {pref && <tr><td className="px-4 py-3 text-slate-400">Preferential ({pref.type})</td><td className="px-4 py-3 text-right font-semibold text-emerald-300">{pct(pref.rate)}</td></tr>}
                    {benefit && <tr><td className="px-4 py-3 text-slate-400">{benefit.scheme} (India, on FOB)</td><td className="px-4 py-3 text-right font-semibold text-cyan-300">+{benefit.rate}%</td></tr>}
                    {duty?.indiaBreakdown && (
                      <>
                        <tr><td className="px-4 py-3 text-slate-400">Basic customs duty (India import)</td><td className="px-4 py-3 text-right">{pct(duty.indiaBreakdown.basicCustomsDuty)}</td></tr>
                        <tr><td className="px-4 py-3 text-slate-400">IGST</td><td className="px-4 py-3 text-right">{pct(duty.indiaBreakdown.igst)}</td></tr>
                      </>
                    )}
                  </tbody>
                </table>
                <div className="px-4 py-3 bg-white/[0.03] text-[11px] text-slate-400 font-mono-display">
                  {imp ? `SOURCE: ${imp.source} · AS OF ${imp.year}` : "NO VERIFIED TARIFF RECORD FOR THIS PAIR"}
                </div>
              </div>
              {duty?.notes?.length > 0 && (
                <ul className="mt-3 text-[12px] text-slate-400 list-disc pl-5 space-y-1">
                  {duty.notes.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
              )}
            </Section>

            {/* Demand */}
            <Section icon={Globe} title={`${c.name} demand & world market`} testId="epc-demand"
              kicker={demand ? `${demand.description || p.name} · ${demand.source}, ${demand.year}` : "Market data unavailable for this HS code."}>
              {demand ? (
                <>
                  <div className="grid sm:grid-cols-3 gap-3">
                    <Fact label="World imports" value={money(demand.worldImportsUSD)} sub={`${demand.year}`} />
                    <Fact label={`${c.name} imports`} value={money(demand.countryImportsUSD)} sub={demand.countryShare != null ? `${demand.countryShare}% of world` : "not separately reported"} />
                    <Fact label="World rank" value={demand.countryRank ? `#${demand.countryRank}` : "—"} sub={demand.countriesReporting ? `of ${demand.countriesReporting} importers` : ""} />
                  </div>
                  <div className="glass rounded-2xl p-4 mt-3">
                    <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400 mb-3">Top importing markets · {demand.year}</div>
                    <div className="space-y-2">
                      {(demand.topImporters || []).map((r) => (
                        <div key={r.country} className="flex items-center justify-between text-[13px]">
                          <span className={r.country === c.name ? "text-cyan-300 font-semibold" : "text-slate-300"}>{r.country}</span>
                          <span className="text-slate-400">{money(r.value)} · {r.share}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : <div className="glass rounded-2xl p-4 text-sm text-slate-400">No trade statistics published for this HS code yet.</div>}
            </Section>

            {/* Documents */}
            <Section icon={FileText} title="Documents & compliance" testId="epc-docs"
              kicker={`The baseline Indian export set, plus what ${c.name} typically asks for on this product.`}>
              <div className="grid sm:grid-cols-2 gap-3">
                {[
                  ["Commercial invoice", "Value, Incoterm, buyer and consignee details"],
                  ["Packing list", "Carton-level weights and dimensions"],
                  ["Shipping bill", "Filed on ICEGATE — carries your IEC and HS code"],
                  ["Bill of lading / AWB", "Title document issued by the carrier"],
                  ["Certificate of origin", pref ? `Mandatory to claim the ${pref.type} rate` : "Proof of Indian origin for customs"],
                  ["Product certification", `Phytosanitary, health, halal or regulatory approval as required by ${c.name}`],
                ].map(([t, s]) => (
                  <div key={t} className="glass rounded-2xl p-4">
                    <div className="text-sm font-semibold">{t}</div>
                    <div className="text-[11px] text-slate-400 mt-1 leading-snug">{s}</div>
                  </div>
                ))}
              </div>
              <Link to="/customs-compliance" data-testid="epc-compliance-link" className="inline-flex items-center gap-2 text-sm text-cyan-300 mt-4 hover:underline">
                Full customs & compliance workspace <ArrowRight size={14} />
              </Link>
            </Section>

            {/* Buyers */}
            <Section icon={Users} title={`Buyers & importers in ${c.name}`} testId="epc-buyers">
              {buyers?.covered ? (
                <>
                  <div className="grid sm:grid-cols-3 gap-3">
                    <Fact label="Screened records" value={buyers.total.toLocaleString()} sub={c.name} />
                    <Fact label="Matching HS family" value={buyers.matchingHs} sub={`HS ${p.primaryHs.slice(0, 4)}xx`} />
                    <Fact label={p.sector} value={buyers.matchingSector} sub="sector matches" />
                  </div>
                  <Link to={`/buyers?country=${encodeURIComponent(c.name)}`} data-testid="epc-buyers-cta" className="btn-primary mt-4 inline-flex">
                    <SealCheck size={16} weight="bold" /> Open Verified Buyer Intelligence
                  </Link>
                </>
              ) : (
                <div data-testid="epc-buyers-waitlist" className="glass-strong rounded-2xl p-5">
                  <div className="text-sm font-semibold">Buyer coverage for {c.name} is being ingested</div>
                  <p className="text-[13px] text-slate-400 mt-2 leading-relaxed">
                    Every buyer record is sanctions-screened and source-cited before we publish it, so we show
                    nothing rather than an unverified list. Meanwhile, the demand table above shows exactly how
                    much {c.name} imports — and our European coverage ({buyers?.total ? "" : "27,000+ screened records"}) is live today.
                  </p>
                  <div className="flex flex-wrap gap-3 mt-4">
                    <Link to="/buyers" data-testid="epc-buyers-explore" className="btn-primary inline-flex">
                      <SealCheck size={16} weight="bold" /> Explore live buyer coverage
                    </Link>
                    <Link to="/contact" data-testid="epc-buyers-notify" className="btn-ghost inline-flex">
                      Notify me when {c.name} goes live
                    </Link>
                  </div>
                </div>
              )}
            </Section>

            {/* Landed cost */}
            <Section icon={Calculator} title="Landed cost & Incoterms" testId="epc-landed"
              kicker="EXW → FOB → CIF → freight → insurance → duty → local charges → landed cost.">
              <div className="glass-strong rounded-2xl p-5 text-sm text-slate-300 leading-relaxed">
                On a CIF shipment to {c.name}, your landed cost is the CIF value plus{" "}
                {effective != null ? <strong>{pct(effective)} duty</strong> : "the destination duty"}{" "}
                plus local VAT/GST, customs handling and inland delivery.
                {benefit && <> Against that, {benefit.scheme} returns <strong>{benefit.rate}% of FOB</strong> to you as a transferable scrip.</>}
              </div>
              <div className="grid sm:grid-cols-2 gap-3 mt-3">
                <ToolLink to={`/tools/landed-cost-calculator?hs=${duty?.hsCode || p.primaryHs}&from=356&to=${c.code}`} icon={Calculator} testId="epc-tool-landed" label="Landed Cost Calculator" note="All 11 Incoterms, your currency" />
                <ToolLink to={`/tools/duty-calculator?hs=${duty?.hsCode || p.primaryHs}&from=356&to=${c.code}`} icon={Scales} testId="epc-tool-duty" label="Duty Calculator" note="Live rates by HS code and market" />
              </div>
            </Section>

            {/* Expos */}
            {expos?.length > 0 && (
              <Section icon={CalendarBlank} title={`Trade fairs in ${c.name}`} testId="epc-expos">
                <div className="space-y-2">
                  {expos.map((e, i) => (
                    <div key={e.id || i} className="glass rounded-2xl p-4 flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="text-sm font-semibold truncate">{e.name || e.title}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{e.city || e.location} · {(e.startDate || e.starts_at || "").slice(0, 10)}</div>
                      </div>
                      <Link to="/expo" className="text-[11px] text-cyan-300 shrink-0 hover:underline">View</Link>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* News */}
            {news?.length > 0 && (
              <Section icon={Newspaper} title={`Latest ${c.name} trade news`} testId="epc-news">
                <div className="space-y-2">
                  {news.map((n, i) => (
                    <div key={n.id || i} className="glass rounded-2xl p-4">
                      <div className="text-sm font-semibold leading-snug">{n.title}</div>
                      <div className="text-[11px] text-slate-400 mt-1">{n.source} · {(n.publishedAt || "").slice(0, 10)}</div>
                    </div>
                  ))}
                </div>
                <Link to="/trade-news" className="inline-flex items-center gap-2 text-sm text-cyan-300 mt-3 hover:underline">
                  All trade news <ArrowRight size={14} />
                </Link>
              </Section>
            )}

            {/* FAQ */}
            <Section title={`${p.name} → ${c.name}: questions exporters ask`} testId="epc-faq">
              <div className="space-y-3">
                {faqs.map((f, i) => (
                  <details key={i} data-testid={`epc-faq-${i}`} className="glass rounded-2xl p-4">
                    <summary className="text-sm font-semibold cursor-pointer">{f.q}</summary>
                    <p className="text-[13px] text-slate-300 mt-2 leading-relaxed">{f.a}</p>
                  </details>
                ))}
              </div>
            </Section>

            <RelatedGuides related={d.related} productName={p.name} countryName={c.name} />
          </div>

          {/* Action rail */}
          <aside className="lg:col-span-4 space-y-3 lg:sticky lg:top-24 lg:self-start" data-testid="epc-actions">
            <div className="glass-strong rounded-2xl p-5">
              <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-cyan-300">Run this trade</div>
              <p className="text-[13px] text-slate-400 mt-2">Take these numbers straight into the tools.</p>
            </div>
            <ToolLink to={`/brain?q=${encodeURIComponent(`Export ${p.name} from India to ${c.name} — duty, documents, buyers and pricing plan`)}`} icon={Brain} testId="epc-rail-brain" label="Ask the Vametra AI Brain" note={`Anything about ${p.name} into ${c.name}`} />
            <ToolLink to={`/tools/hsn-finder?hs=${duty?.hsCode || p.primaryHs}&to=${c.code}`} icon={FileText} testId="epc-rail-hs" label="HS Code Finder" note="All 5,606 HS codes, searchable" />
            <ToolLink to={`/tools/duty-calculator?hs=${duty?.hsCode || p.primaryHs}&from=356&to=${c.code}`} icon={Scales} testId="epc-rail-duty" label="Duty Calculator" note="Confirm the applied rate" />
            <ToolLink to={`/tools/landed-cost-calculator?hs=${duty?.hsCode || p.primaryHs}&from=356&to=${c.code}`} icon={Calculator} testId="epc-rail-landed" label="Landed Cost" note="Quote with confidence" />
            <ToolLink to={`/buyers?hs=${duty?.hsCode || p.primaryHs}&country=${encodeURIComponent(c.name)}`} icon={Users} testId="epc-rail-buyers" label="Verified Buyers" note="Screened, source-cited records" />
            <ToolLink to="/command-center" icon={Truck} testId="epc-rail-cc" label="Trade Command Center" note="Run the whole shipment" />
            <ToolLink to={`/countries/${c.slug}`} icon={Globe} testId="epc-rail-country" label={`${c.name} trade profile`} note="Tariffs, partners, compliance" />
            <ToolLink to={`/corridors/india-to-${c.slug}`} icon={ArrowRight} testId="epc-rail-corridor" label={`India → ${c.name}`} note="Corridor playbook" />

            <div className="glass rounded-2xl p-4">
              <div className="text-[10px] font-mono-display tracking-[0.2em] uppercase text-slate-400 mb-2">Data sources</div>
              <ul className="space-y-1.5 text-[11px] text-slate-400">
                {(d.sources || []).map((s, i) => (
                  <li key={i}>{s.name} <span className="text-slate-500">· {s.asOf}</span></li>
                ))}
              </ul>
              <p className="text-[10px] text-slate-500 mt-3 leading-relaxed">{d.disclaimer}</p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
