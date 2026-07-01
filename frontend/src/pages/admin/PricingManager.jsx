import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { CurrencyCircleDollar, FloppyDisk, ChartLineUp, CreditCard, Star, EnvelopeSimple } from "@phosphor-icons/react";

const PLAN_ORDER = ["download", "monthly", "annual"];
const REGIONS = [
  { key: "IN", label: "India (₹)" },
  { key: "INTL", label: "International ($)" },
];

export default function PricingManager() {
  const [cfg, setCfg] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => {
    adminApi.get("/pricing/admin").then((r) => setCfg(r.data)).catch(() => {});
    adminApi.get("/pricing/admin/analytics").then((r) => setAnalytics(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  if (!cfg) return <div className="text-slate-400">Loading pricing engine…</div>;

  const setPlanPrice = (plan, region, val) => {
    setCfg((c) => ({ ...c, plans: { ...c.plans, [plan]: { ...c.plans[plan], [region]: val } } }));
  };
  const setPlanField = (plan, field, val) => {
    setCfg((c) => ({ ...c, plans: { ...c.plans, [plan]: { ...c.plans[plan], [field]: val } } }));
  };
  const toggleGateway = (name) => {
    setCfg((c) => ({ ...c, gateways: { ...c.gateways, [name]: { ...c.gateways[name], enabled: !c.gateways[name].enabled } } }));
  };
  const setSetting = (k, v) => setCfg((c) => ({ ...c, settings: { ...c.settings, [k]: v } }));

  const save = async () => {
    setSaving(true); setMsg("");
    try {
      const plans = {};
      for (const p of PLAN_ORDER) {
        plans[p] = {
          label: cfg.plans[p].label,
          tagline: cfg.plans[p].tagline || "",
          active: cfg.plans[p].active !== false,
          IN: Number(cfg.plans[p].IN) || 0,
          INTL: Number(cfg.plans[p].INTL) || 0,
        };
      }
      await adminApi.put("/pricing/admin", {
        plans,
        gateways: cfg.gateways,
        settings: cfg.settings,
      });
      setMsg("Saved — prices are now live everywhere (site, checkout, Stripe, Razorpay).");
      load();
    } catch (e) {
      setMsg(e?.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6" data-testid="pricing-manager">
      <div className="glass-strong rounded-3xl p-6">
        <div className="font-display font-bold text-xl flex items-center gap-2 mb-1"><CurrencyCircleDollar size={20} weight="duotone" className="text-cyan-300" /> Pricing Engine</div>
        <p className="text-xs text-slate-400 mb-5">Single source of truth for every price. Changes here sync instantly across the website, checkout, Stripe, Razorpay and future apps. No price is hardcoded anywhere else.</p>

        <div className="space-y-4">
          {PLAN_ORDER.map((plan) => {
            const p = cfg.plans[plan];
            return (
              <div key={plan} className="glass rounded-2xl p-4" data-testid={`pricing-plan-${plan}`}>
                <div className="flex items-center gap-3 flex-wrap mb-3">
                  <input
                    data-testid={`pricing-${plan}-label`}
                    value={p.label || ""} onChange={(e) => setPlanField(plan, "label", e.target.value)}
                    className="glass rounded-lg px-3 py-1.5 text-sm font-semibold w-48" />
                  <span className="text-[11px] font-mono-display uppercase tracking-widest text-slate-500">{p.interval}</span>
                  <label className="ml-auto flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                    <input type="checkbox" checked={p.active !== false} onChange={(e) => setPlanField(plan, "active", e.target.checked)} className="w-4 h-4 accent-cyan-400" data-testid={`pricing-${plan}-active`} />
                    Active
                  </label>
                </div>
                <input
                  data-testid={`pricing-${plan}-tagline`}
                  value={p.tagline || ""} onChange={(e) => setPlanField(plan, "tagline", e.target.value)}
                  placeholder="Tagline shown on pricing card"
                  className="glass rounded-lg px-3 py-1.5 text-xs w-full mb-3" />
                <div className="grid sm:grid-cols-2 gap-3">
                  {REGIONS.map((r) => (
                    <div key={r.key}>
                      <div className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400 mb-1">{r.label}</div>
                      <input
                        data-testid={`pricing-${plan}-${r.key}`}
                        type="number" min="0" step="0.01"
                        value={p[r.key]} onChange={(e) => setPlanPrice(plan, r.key, e.target.value)}
                        className="glass rounded-xl px-3 py-2 w-full text-sm font-mono-display" />
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="glass-strong rounded-3xl p-6">
        <div className="font-display font-bold text-lg flex items-center gap-2 mb-4"><CreditCard size={18} weight="duotone" className="text-cyan-300" /> Payment Gateways</div>
        <div className="grid sm:grid-cols-2 gap-3">
          {Object.entries(cfg.gateways || {}).map(([name, g]) => (
            <button key={name} data-testid={`pricing-gateway-${name}`} onClick={() => toggleGateway(name)}
              className={`flex items-center justify-between glass rounded-xl px-4 py-3 text-sm transition-all ${g.enabled ? "border-emerald-400/40" : "opacity-60"}`}>
              <span>
                <span className="font-medium">{g.label || name}</span>
                <span className="block text-[11px] text-slate-500 font-mono-display">{(g.regions || []).join(", ")}</span>
              </span>
              <span className={`text-[10px] font-mono-display uppercase px-2 py-0.5 rounded-full ${g.enabled ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>{g.enabled ? "Enabled" : "Disabled"}</span>
            </button>
          ))}
        </div>
        <p className="text-[11px] text-slate-500 mt-3">Razorpay activates for Indian users once its API keys are added to the environment. Future gateways plug into the same engine.</p>
      </div>

      <div className="glass-strong rounded-3xl p-6">
        <div className="font-display font-bold text-lg flex items-center gap-2 mb-4"><Star size={18} weight="duotone" className="text-cyan-300" /> Monetization Settings</div>
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input data-testid="pricing-free-first" type="checkbox" checked={cfg.settings?.freeFirstDownload !== false} onChange={(e) => setSetting("freeFirstDownload", e.target.checked)} className="w-5 h-5 accent-cyan-400" />
            <span className="text-sm text-slate-300">First report download is free</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input data-testid="pricing-email-capture" type="checkbox" checked={cfg.settings?.emailCaptureBeforePaywall !== false} onChange={(e) => setSetting("emailCaptureBeforePaywall", e.target.checked)} className="w-5 h-5 accent-cyan-400" />
            <span className="text-sm text-slate-300 flex items-center gap-1"><EnvelopeSimple size={14} /> Capture email before showing the paywall</span>
          </label>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-slate-300">"Most Popular" plan:</span>
            <select data-testid="pricing-most-popular" value={cfg.settings?.mostPopular || "annual"} onChange={(e) => setSetting("mostPopular", e.target.value)}
              className="glass rounded-xl px-3 py-2 text-sm bg-[#0a1024] text-white">
              {PLAN_ORDER.map((p) => <option key={p} value={p} className="bg-[#0a1024]">{cfg.plans[p]?.label || p}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <button data-testid="pricing-save" onClick={save} disabled={saving} className="btn-primary disabled:opacity-50"><FloppyDisk size={16} weight="bold" /> {saving ? "Saving…" : "Save pricing"}</button>
        {msg && <span data-testid="pricing-save-msg" className="text-sm text-emerald-300">{msg}</span>}
      </div>

      {analytics && (
        <div className="glass-strong rounded-3xl p-6" data-testid="pricing-analytics">
          <div className="font-display font-bold text-lg flex items-center gap-2 mb-4"><ChartLineUp size={18} weight="duotone" className="text-cyan-300" /> Paywall Funnel</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { l: "Paywall views", v: analytics.funnel?.paywall_view || 0 },
              { l: "Emails captured", v: analytics.emailCaptures || 0 },
              { l: "Checkouts started", v: analytics.funnel?.checkout_start || 0 },
              { l: "Conversion", v: `${analytics.conversionPct || 0}%` },
            ].map((s) => (
              <div key={s.l} className="glass rounded-xl px-4 py-3">
                <div className="text-2xl font-display font-extrabold text-cyan-300">{s.v}</div>
                <div className="text-[11px] text-slate-400 uppercase tracking-widest font-mono-display mt-1">{s.l}</div>
              </div>
            ))}
          </div>
          {analytics.recentCaptures?.length > 0 && (
            <div className="mt-4">
              <div className="text-[11px] font-mono-display uppercase tracking-widest text-slate-400 mb-2">Recent email captures</div>
              <div className="space-y-1 max-h-48 overflow-auto">
                {analytics.recentCaptures.map((c, i) => (
                  <div key={i} className="text-sm flex items-center gap-2 glass rounded-lg px-3 py-1.5">
                    <span className="text-cyan-300">{c.email}</span>
                    <span className="text-[11px] text-slate-500 ml-auto">{c.region} · {String(c.createdAt).slice(0, 10)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
