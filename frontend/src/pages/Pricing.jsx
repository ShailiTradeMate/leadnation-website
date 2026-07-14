import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useProject } from "@/lib/ProjectContext";
import SEO, { organizationSchema, breadcrumbSchema, faqSchema } from "@/components/SEO";
import { Check, X, Star, CircleNotch, Lightning, ArrowRight } from "@phosphor-icons/react";

const detectRegion = () => {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    if (tz.includes("Kolkata") || tz.includes("Calcutta")) return "IN";
  } catch (_) {}
  return "INTL";
};

const fmt = (symbol, amount) => `${symbol}${Number(amount).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

export default function Pricing() {
  const P = useProject();
  const [region, setRegion] = useState(detectRegion());
  const [cfg, setCfg] = useState(null);
  const [busy, setBusy] = useState("");

  const s = () => ({ headers: { "X-Trade-Session": P?.session } });

  useEffect(() => {
    api.get("/pricing/config", { params: { region } }).then((r) => setCfg(r.data)).catch(() => {});
  }, [region]);

  useEffect(() => {
    api.post("/pricing/track", { event: "pricing_page_view", region }, s()).catch(() => {});
  }, [region]);

  const startCheckout = async (planKey) => {
    if (planKey === "download") return; // download is purchased inside a project
    setBusy(planKey);
    try {
      await api.post("/pricing/track", { event: "checkout_start", plan: planKey, region }, s()).catch(() => {});
      const { data } = await api.post("/payments/checkout", { kind: planKey, region, origin: window.location.origin }, s());
      window.location.href = data.url;
    } catch (_) { setBusy(""); }
  };

  if (!cfg) return <section className="min-h-[70vh] grid place-items-center"><CircleNotch size={28} className="animate-spin text-cyan-300" /></section>;

  const mostPopular = cfg.settings?.mostPopular || "annual";
  const subPlans = cfg.plans.filter((p) => p.key !== "download");
  const featureCols = ["download", "monthly", "annual"].filter((k) => cfg.plans.some((p) => p.key === k));

  const cell = (v) => {
    if (v === true) return <Check size={18} weight="bold" className="text-emerald-400 mx-auto" />;
    if (v === false) return <X size={16} className="text-slate-600 mx-auto" />;
    return <span className="text-slate-300 text-xs">{v}</span>;
  };

  return (
    <section className="max-w-6xl mx-auto px-6 sm:px-10 pt-16 pb-28" data-testid="pricing-page">
      <SEO
        title="Pricing · LeadNation Trade Intelligence Plans"
        description="Simple, transparent pricing for LeadNation. Your first trade report is free. Go unlimited with Monthly or Annual Pro plans — customs duties, HS codes, landed cost, expos and trade news. Cancel anytime."
        path="/pricing"
        keywords="LeadNation pricing, trade intelligence pricing, export software price, customs duty calculator plans, trade report subscription"
        schema={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Pricing", path: "/pricing" },
          ]),
          organizationSchema,
          faqSchema([
            { q: "Is LeadNation free to use?", a: "Yes — you can explore the platform and generate your first trade report for free. Pro plans unlock unlimited reports and premium intelligence." },
            { q: "Which payment methods are supported?", a: "International customers pay securely via Stripe (USD); customers in India can pay via Razorpay (INR)." },
            { q: "Can I cancel anytime?", a: "Yes. Pro subscriptions can be cancelled anytime and remain active until the end of the billing period." },
          ]),
        ]}
      />

      <div className="text-center max-w-2xl mx-auto">
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Plans & Pricing</div>
        <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl mt-3">Unlock the world's trade desk</h1>
        <p className="text-slate-400 text-base mt-4">Your first Trade Report is free. Go unlimited with a Pro plan — cancel anytime.</p>
      </div>

      {/* Region toggle */}
      <div className="flex justify-center mt-8">
        <div className="glass-strong rounded-full p-1 flex" data-testid="pricing-region-toggle">
          {[{ k: "IN", l: "🇮🇳 India" }, { k: "INTL", l: "🌍 International" }].map((r) => (
            <button key={r.k} data-testid={`pricing-region-${r.k}`} onClick={() => setRegion(r.k)}
              className={`px-5 py-2 rounded-full text-sm transition-all ${region === r.k ? "bg-cyan-400 text-[#04121f] font-semibold" : "text-slate-300 hover:text-white"}`}>
              {r.l}
            </button>
          ))}
        </div>
      </div>

      {/* Plan cards */}
      <div className="grid md:grid-cols-3 gap-5 mt-10 items-stretch">
        {cfg.plans.map((p) => {
          const popular = p.key === mostPopular;
          const annualSave = p.key === "annual" && cfg.annualSavingsPct ? cfg.annualSavingsPct : null;
          return (
            <div key={p.key} data-testid={`pricing-card-${p.key}`}
              className={`relative glass-strong rounded-3xl p-7 flex flex-col ${popular ? "border-2 border-cyan-400/60 shadow-[0_0_40px_-8px_rgba(0,194,255,0.4)]" : ""}`}>
              {popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-cyan-400 text-[#04121f] text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-full flex items-center gap-1" data-testid="pricing-popular-badge">
                  <Star size={12} weight="fill" /> Most Popular
                </div>
              )}
              <div className="font-display font-bold text-xl">{p.label}</div>
              <div className="text-xs text-slate-400 mt-1 min-h-[2.5rem]">{p.tagline}</div>
              <div className="flex items-end gap-1 mt-4">
                <span className="font-display font-extrabold text-4xl">{fmt(p.symbol, p.amount)}</span>
                <span className="text-slate-400 text-sm mb-1">/{p.interval === "one_time" ? "report" : p.interval === "year" ? "yr" : "mo"}</span>
              </div>
              {annualSave && <div className="text-[11px] text-emerald-300 mt-1">Save {annualSave}% vs monthly</div>}

              {p.key === "download" ? (
                <Link to="/command-center" data-testid="pricing-cta-download"
                  className="btn-ghost justify-center mt-6">Build a report <ArrowRight size={15} weight="bold" /></Link>
              ) : (
                <button data-testid={`pricing-cta-${p.key}`} onClick={() => startCheckout(p.key)} disabled={busy === p.key}
                  className={`${popular ? "btn-primary" : "btn-ghost"} justify-center mt-6 disabled:opacity-50`}>
                  {busy === p.key ? <CircleNotch size={15} className="animate-spin" /> : <Lightning size={15} weight="bold" />} Get {p.label}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Feature comparison table */}
      {cfg.features?.length > 0 && (
        <div className="glass-strong rounded-3xl p-6 sm:p-8 mt-12 overflow-x-auto" data-testid="pricing-comparison">
          <div className="font-display font-bold text-xl mb-5">Compare plans</div>
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 font-medium text-slate-300">Feature</th>
                {featureCols.map((k) => {
                  const plan = cfg.plans.find((p) => p.key === k);
                  return <th key={k} className="py-3 text-center font-display font-bold">{plan?.label || k}</th>;
                })}
              </tr>
            </thead>
            <tbody>
              {cfg.features.map((f, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="py-3 text-slate-300">{f.label}</td>
                  {featureCols.map((k) => <td key={k} className="py-3 text-center">{cell(f[k])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-center text-xs text-slate-500 mt-8">
        Prices shown in {region === "IN" ? "INR (₹)" : "USD ($)"}. Payments processed securely via {cfg.gateway === "razorpay" ? "Razorpay" : "Stripe"}. One login shared with the LeadNation app.
      </p>
      <p className="text-center text-[11px] text-slate-600 mt-2" data-testid="pricing-legal">
        By purchasing you agree to our <Link to="/legal/terms" className="text-cyan-300 hover:underline">Terms</Link> and <Link to="/legal/refund" className="text-cyan-300 hover:underline">Refund &amp; Cancellation Policy</Link>.
      </p>
    </section>
  );
}
