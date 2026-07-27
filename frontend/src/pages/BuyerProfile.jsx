import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import SEO from "@/components/SEO";
import { TrustBadge } from "@/components/BuyerCard";
import { fetchBuyer, claimBuyer, TRUST_COLORS } from "@/lib/vbieApi";
import {
  ShieldCheck, MapPin, Package, Buildings, ArrowLeft, LinkSimple,
  CheckCircle, FileText, Handshake, Sparkle,
} from "@phosphor-icons/react";

export default function BuyerProfile() {
  const { geid } = useParams();
  const [b, setB] = useState(null);
  const [err, setErr] = useState(false);
  const [showClaim, setShowClaim] = useState(false);

  useEffect(() => {
    setB(null); setErr(false);
    fetchBuyer(geid).then(setB).catch(() => setErr(true));
  }, [geid]);

  if (err) return <Centered>Buyer not found. <Link to="/buyers" className="text-cyan-300 underline">Back to search</Link></Centered>;
  if (!b) return <Centered>Loading buyer intelligence…</Centered>;

  const trust = b.trust || {};

  return (
    <>
      <SEO
        title={`${b.display_name} · Verified Buyer Intelligence`}
        description={`Verified buyer profile for ${b.display_name} (${b.country_name}) — sector ${b.sector}, trust score ${trust.score}. Cited source evidence and trade intelligence by LeadNation.`}
        path={`/buyers/${geid}`}
        keywords={`${b.display_name}, ${b.sector} importer, verified buyer ${b.country_name}`}
      />

      <section className="max-w-6xl mx-auto px-6 sm:px-10 pt-24 pb-16">
        <Link to="/buyers" data-testid="buyer-back" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors mb-6">
          <ArrowLeft size={15} weight="bold" /> All buyers
        </Link>

        {/* Header */}
        <div data-testid="buyer-profile-header" className="glass-strong rounded-3xl p-7 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300/80">{b.sector}</div>
              <h1 className="mt-2 font-display font-black text-3xl sm:text-4xl leading-tight flex items-center gap-3">
                <Buildings size={30} weight="duotone" className="text-violet-300" /> {b.display_name}
              </h1>
              <div className="mt-2 text-sm text-slate-400 flex flex-wrap items-center gap-x-4 gap-y-1">
                <span className="flex items-center gap-1.5"><MapPin size={14} weight="duotone" /> {b.city} · {b.country_name}</span>
                <span className="capitalize">{b.role}</span>
                {b.size && <span>{b.size}</span>}
              </div>
            </div>
            <TrustBadge trust={trust} size="lg" />
          </div>

          {b.sample && (
            <div className="mt-5 text-xs text-amber-300/90 bg-amber-500/10 border border-amber-400/20 rounded-xl px-4 py-2.5">
              Illustrative directory record with cited sources. Connector-verified live intelligence is being onboarded.
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <button data-testid="buyer-claim-btn" onClick={() => setShowClaim(true)} className="btn-primary">
              <Handshake size={15} weight="bold" /> Request introduction
            </button>
            {b.website && (
              <a href={b.website} target="_blank" rel="noreferrer" className="btn-ghost inline-flex items-center gap-1.5">
                <LinkSimple size={15} weight="bold" /> Website
              </a>
            )}
          </div>
        </div>

        <div className="mt-6 grid lg:grid-cols-3 gap-6">
          {/* Trust breakdown */}
          <div className="lg:col-span-1 glass rounded-3xl p-6">
            <h2 className="font-display font-bold text-lg flex items-center gap-2">
              <ShieldCheck size={18} weight="fill" className="text-cyan-300" /> Trust breakdown
            </h2>
            <div className="mt-4 flex items-end gap-3">
              <span className="font-display font-black text-5xl">{trust.score}</span>
              <span className={`mb-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono-display uppercase tracking-widest border ${TRUST_COLORS[trust.color] || TRUST_COLORS.slate}`}>{trust.band}</span>
            </div>
            <div className="mt-4 space-y-2">
              {(trust.factors || []).map((f, i) => (
                <div key={i} data-testid={`trust-factor-${i}`} className="flex items-start justify-between gap-3 text-sm border-b border-white/5 pb-2">
                  <div>
                    <div className="text-slate-200">{f.label}</div>
                    <div className="text-[11px] text-slate-500">{f.detail}</div>
                  </div>
                  <span className={`font-mono-display shrink-0 ${f.points < 0 ? "text-rose-300" : "text-emerald-300"}`}>
                    {f.points > 0 ? "+" : ""}{f.points}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Profile + products */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-3xl p-6">
              <h2 className="font-display font-bold text-lg flex items-center gap-2"><Package size={18} weight="duotone" className="text-violet-300" /> Products of interest</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(b.products || []).map((p) => <span key={p} className="text-sm px-3 py-1.5 rounded-full bg-white/5 text-slate-200">{p}</span>)}
              </div>
              <div className="mt-5 grid sm:grid-cols-2 gap-4 text-sm">
                <KV label="HS families" value={(b.hs_families || []).join(", ")} />
                <KV label="Trade corridors" value={(b.corridors || []).join(", ")} />
                <KV label="Market" value={b.country_name} />
                <KV label="Role" value={b.role} cap />
              </div>
            </div>

            {/* Evidence */}
            <div className="glass rounded-3xl p-6">
              <h2 className="font-display font-bold text-lg flex items-center gap-2"><FileText size={18} weight="duotone" className="text-cyan-300" /> Source evidence</h2>
              <p className="text-xs text-slate-500 mt-1">Every fact is traceable to a cited source — the core of verifiable buyer intelligence.</p>
              <div className="mt-4 space-y-3">
                {(b.provenance || []).map((p, i) => (
                  <div key={i} data-testid={`buyer-evidence-${i}`} className="flex items-start gap-3 border border-white/5 rounded-2xl p-3.5">
                    <CheckCircle size={18} weight="fill" className="text-emerald-300 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-slate-100">{p.source_name}</span>
                        <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/5 text-slate-400">{p.source_tier}</span>
                        <span className="text-[10px] text-slate-500">→ {p.field}</span>
                      </div>
                      {p.attribution && <div className="text-[11px] text-slate-500 mt-0.5">{p.attribution}</div>}
                      {p.source_url && <a href={p.source_url} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-300 underline break-all">{p.source_url}</a>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {showClaim && <ClaimModal geid={geid} buyerName={b.display_name} onClose={() => setShowClaim(false)} />}
    </>
  );
}

function ClaimModal({ geid, buyerName, onClose }) {
  const [form, setForm] = useState({ name: "", email: "", company: "", role: "", message: "" });
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.email.trim()) return;
    setBusy(true);
    try { await claimBuyer(geid, form); setDone(true); } catch (_) { /* noop */ } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div data-testid="buyer-claim-modal" className="glass-strong rounded-3xl p-7 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        {done ? (
          <div className="text-center py-6">
            <Sparkle size={34} weight="fill" className="text-cyan-300 mx-auto" />
            <h3 className="mt-3 font-display font-bold text-xl">Request received</h3>
            <p className="text-sm text-slate-400 mt-2">Our trade desk will reach out about an introduction to {buyerName}.</p>
            <button data-testid="claim-close" onClick={onClose} className="btn-primary mt-5">Done</button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <h3 className="font-display font-bold text-xl">Request an introduction</h3>
            <p className="text-sm text-slate-400">Connect with {buyerName} through the LeadNation trade desk.</p>
            <input data-testid="claim-name" required placeholder="Your name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none text-sm" />
            <input data-testid="claim-email" required type="email" placeholder="Work email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none text-sm" />
            <input data-testid="claim-company" placeholder="Your company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} className="w-full glass rounded-xl px-4 py-3 outline-none text-sm" />
            <textarea data-testid="claim-message" placeholder="What would you like to supply? (optional)" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} rows={3} className="w-full glass rounded-xl px-4 py-3 outline-none text-sm" />
            <button data-testid="claim-submit" disabled={busy} className="btn-primary w-full justify-center">{busy ? "Sending…" : "Send request"}</button>
          </form>
        )}
      </div>
    </div>
  );
}

function KV({ label, value, cap }) {
  return (
    <div>
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-500">{label}</div>
      <div className={`text-slate-200 ${cap ? "capitalize" : ""}`}>{value || "—"}</div>
    </div>
  );
}

function Centered({ children }) {
  return <div className="min-h-[60vh] flex items-center justify-center text-slate-400 text-sm gap-2">{children}</div>;
}
