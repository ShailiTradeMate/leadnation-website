import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero, SectionLabel } from "@/components/PageHero";
import { Card } from "@/components/ToolShell";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { ArrowRight, CheckCircle, FileText, Wrench, PaperPlaneTilt, CaretDown, Briefcase } from "@phosphor-icons/react";

export function ServicesHub() {
  const [list, setList] = useState([]);
  useEffect(() => { api.get("/services").then((r) => setList(r.data)); }, []);

  const grouped = list.reduce((acc, s) => { (acc[s.category] = acc[s.category] || []).push(s); return acc; }, {});

  return (
    <>
      <SEO title="Business Services · RCMC, GST, IEC, Export Consulting"
        description="LeadNation Business Services — RCMC, GST, IEC and company registration handled by certified CAs. Plus export, import, compliance, market-entry and sourcing consulting."
        path="/services"
        keywords="RCMC registration, GST registration, IEC code, company registration, export consulting, import consulting, market entry"
      />
      <PageHero testIdPrefix="services" label="Business Services"
        title="Compliance, registrations, consulting. Done."
        sub="A LeadNation CA handles your government documentation and a certified consultant guides your global trade — end to end."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 space-y-10">
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat}>
            <h2 className="font-display font-bold text-2xl">{cat}</h2>
            <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {items.map((s) => (
                <Link key={s.slug} to={`/services/${s.slug}`} data-testid={`services-card-${s.slug}`}
                  className="group glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
                  <div className="h-40 relative overflow-hidden">
                    <img src={s.image} alt={s.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                  </div>
                  <div className="p-5">
                    <h3 className="font-display font-bold text-lg">{s.name}</h3>
                    <p className="text-xs text-slate-400 mt-1">{s.tagline}</p>
                    <div className="mt-3 flex items-center justify-between text-xs">
                      <span className="text-cyan-300 font-mono-display tracking-widest">FROM {s.priceFrom}</span>
                      <ArrowRight size={14} className="text-cyan-300 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function ServiceDetail() {
  const { slug } = useParams();
  const [s, setS] = useState(null);
  const [nf, setNf] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);
  const [form, setForm] = useState({ service: slug, name: "", email: "", phone: "", country: "India", company: "", message: "" });
  const [submitted, setSubmitted] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    setS(null); setNf(false); setSubmitted(false);
    api.get(`/service/${slug}`).then((r) => r.data?.error ? setNf(true) : setS(r.data)).catch(() => setNf(true));
    setForm((f) => ({ ...f, service: slug }));
  }, [slug]);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await api.post("/service-request", form);
      trackEvent("service_request_submitted", { service: slug });
      setSubmitted(true);
    } catch (_) { setErr("Could not submit — try WhatsApp."); }
  };

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">Service not found</h1><Link to="/services" className="btn-primary mt-6 inline-flex">Browse services</Link></div>;
  if (!s) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={`${s.name} · ${s.tagline}`}
        description={s.overview.substring(0, 160)}
        path={`/services/${s.slug}`}
        keywords={`${s.name}, ${s.category}, ${s.name} India, ${s.name} online`}
        schema={{ "@context": "https://schema.org", "@type": "Service", name: s.name, description: s.overview, provider: { "@type": "Organization", name: "LeadNation" } }}
      />

      <section className="relative pt-16 pb-10">
        <div className="aurora" />
        <div className="relative max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-7">
            <SectionLabel>{s.category}</SectionLabel>
            <h1 data-testid="service-title" className="font-display font-extrabold tracking-tight text-5xl sm:text-6xl mt-4">{s.name}</h1>
            <p className="mt-4 text-slate-300 text-lg">{s.tagline}</p>
            <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 text-sm">
              Starts at {s.priceFrom}
            </div>
          </div>
          <div className="lg:col-span-5">
            <div className="rounded-3xl overflow-hidden border border-white/10 h-[240px] relative">
              <img src={s.image} alt={s.name} className="absolute inset-0 w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#050816] via-transparent to-transparent" />
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7 space-y-5">
          <Card title="Service overview" Icon={Briefcase}><p className="mt-3 text-slate-300 leading-relaxed">{s.overview}</p></Card>
          <Card title="Key benefits"><ul className="mt-3 space-y-2 text-sm">{s.benefits.map((b, i) => <li key={i} className="flex gap-2"><CheckCircle size={16} weight="fill" className="text-cyan-300 mt-0.5" />{b}</li>)}</ul></Card>
          <Card title="Documents required" Icon={FileText}><ul className="mt-3 grid sm:grid-cols-2 gap-2 text-sm">{s.documents.map((d, i) => <li key={i} className="glass rounded-xl px-3 py-2">{d}</li>)}</ul></Card>
          <Card title="Process flow" Icon={Wrench}>
            <ol className="mt-3 space-y-3">
              {s.process.map((p, i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="w-7 h-7 shrink-0 rounded-full grid place-items-center bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-white/10 text-xs font-mono-display tracking-widest">{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-sm pt-0.5">{p}</span>
                </li>
              ))}
            </ol>
          </Card>
          <Card title="Frequently asked">
            <ul className="mt-3 divide-y divide-white/5">
              {s.faqs.map((f, i) => (
                <li key={i}>
                  <button data-testid={`service-faq-${i}`} onClick={() => setOpenFaq(openFaq === i ? -1 : i)} className="w-full text-left py-3 flex items-center justify-between">
                    <span className="text-sm font-medium pr-4">{f.q}</span>
                    <CaretDown size={14} className={`text-cyan-300 transition-transform ${openFaq === i ? "rotate-180" : ""}`} />
                  </button>
                  {openFaq === i && <div className="pb-3 text-sm text-slate-300">{f.a}</div>}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <aside className="lg:col-span-5">
          <div className="glass-strong rounded-3xl p-6 sticky top-24">
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Get started</div>
            <h2 className="font-display font-bold text-2xl mt-1">Request {s.name}</h2>
            <p className="text-xs text-slate-400 mt-1">A LeadNation CA will reach you within 4 working hours.</p>
            {!submitted ? (
              <form onSubmit={submit} className="mt-5 space-y-3">
                {[
                  ["name", "Full name", true],
                  ["email", "Email", true, "email"],
                  ["phone", "Phone / WhatsApp", false],
                  ["company", "Company (optional)", false],
                  ["country", "Country", false],
                ].map(([k, l, req, type]) => (
                  <input key={k} data-testid={`service-${k}`} required={req} type={type || "text"} value={form[k] || ""} placeholder={l + (req ? " *" : "")}
                    onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                    className="w-full glass rounded-xl px-4 py-3 outline-none placeholder:text-slate-500 text-sm" />
                ))}
                <textarea data-testid="service-message" rows={3} placeholder="Anything specific?" value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  className="w-full glass rounded-xl px-4 py-3 outline-none placeholder:text-slate-500 text-sm" />
                <button data-testid="service-submit" className="btn-primary w-full justify-center">Submit request <PaperPlaneTilt size={14} weight="bold" /></button>
                {err && <div className="text-rose-300 text-sm">{err}</div>}
              </form>
            ) : (
              <div data-testid="service-success" className="mt-5 p-5 rounded-2xl bg-emerald-500/10 border border-emerald-400/30">
                <div className="text-emerald-300 font-display font-bold">Request received ✓</div>
                <p className="text-sm text-slate-300 mt-2">A LeadNation CA will reach out shortly. You can also reach us instantly on WhatsApp.</p>
                <a href="https://wa.me/918237161088" target="_blank" rel="noopener noreferrer" className="btn-primary mt-4 w-full justify-center">Chat on WhatsApp</a>
              </div>
            )}
          </div>
        </aside>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12"><DownloadCTA /></section>
    </>
  );
}
