import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import SEO from "@/components/SEO";
import { TrustBadge } from "@/components/BuyerCard";
import { fetchBuyer, claimBuyer, watchBuyer, unwatchBuyer, revealBuyerContact, TRUST_COLORS } from "@/lib/vbieApi";
import { useAuth } from "@/lib/AuthContext";
import { toast } from "sonner";
import {
  ShieldCheck, MapPin, Package, Buildings, ArrowLeft, LinkSimple,
  CheckCircle, FileText, Handshake, Sparkle, Lock, Crown, Warning,
  Gauge, Clock, Stack, Certificate, Fingerprint, BellSimple,
  EnvelopeSimple, Phone, Globe, IdentificationCard, AddressBook,
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
                <span className="flex items-center gap-1.5"><MapPin size={14} weight="duotone" /> {b.city ? `${b.city} · ` : ""}{b.country_name}</span>
                <span className="capitalize">{b.role}</span>
                {b.size && <span>{b.size}</span>}
                {b.last_verified && <span data-testid="buyer-last-verified">Verified {new Date(b.last_verified).toLocaleDateString()}</span>}
              </div>
            </div>
            <TrustBadge trust={trust} size="lg" />
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button data-testid="buyer-claim-btn" onClick={() => setShowClaim(true)} className="btn-primary">
              <Handshake size={15} weight="bold" /> Request introduction
            </button>
            <WatchButton geid={geid} />
          </div>
        </div>

        {b.source_warning && (
          <div data-testid="buyer-source-warning" className="mt-5 flex items-start gap-2.5 rounded-2xl border border-amber-400/25 bg-amber-400/[0.06] p-4 text-xs text-amber-200/90">
            <Warning size={16} weight="fill" className="text-amber-300 shrink-0 mt-0.5" />
            <span><b>Source: {b.primary_source || "official public sources"}.</b> {b.source_warning}</span>
          </div>
        )}

        {b.intelligence && <IntelligencePanel intel={b.intelligence} sources={b.evidence_sources} />}

        {b.locked ? (
          <PaywallGate reason={b.lock_reason} buyer={b} />
        ) : (
          <>
            <ContactReveal geid={geid} buyerName={b.display_name} />
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

              {/* Evidence — generic, category-level only. No source name/link is ever shown. */}
              <div className="glass rounded-3xl p-6">
                <h2 className="font-display font-bold text-lg flex items-center gap-2"><FileText size={18} weight="duotone" className="text-cyan-300" /> Verified against official records</h2>
                <p className="text-xs text-slate-500 mt-1">LeadNation independently verifies every buyer against official government sources. We are your single, verified point of contact — no third-party links.</p>
                <div className="mt-4 space-y-3">
                  {(b.evidence || []).map((p, i) => (
                    <div key={i} data-testid={`buyer-evidence-${i}`} className="flex items-start gap-3 border border-white/5 rounded-2xl p-3.5">
                      <CheckCircle size={18} weight="fill" className="text-emerald-300 shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-slate-100">{p.source_label}</span>
                          <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/5 text-slate-400">{p.tier_label}</span>
                          {p.field && <span className="text-[10px] text-slate-500">→ {p.field}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          </>
        )}
      </section>

      {showClaim && <ClaimModal geid={geid} buyerName={b.display_name} onClose={() => setShowClaim(false)} />}
    </>
  );
}

function WatchButton({ geid }) {
  const { isAuthed } = useAuth();
  const [watching, setWatching] = useState(false);
  const [busy, setBusy] = useState(false);
  const toggle = async () => {
    if (!isAuthed) { toast.error("Sign in to watch this buyer for change alerts"); return; }
    setBusy(true);
    try {
      if (watching) { await unwatchBuyer(geid); setWatching(false); toast.success("Removed from watchlist"); }
      else { await watchBuyer(geid); setWatching(true); toast.success("You'll be alerted when this buyer changes"); }
    } catch { toast.error("Could not update watchlist"); }
    setBusy(false);
  };
  return (
    <button data-testid="buyer-watch-btn" onClick={toggle} disabled={busy}
      className="btn-ghost inline-flex items-center gap-1.5">
      <BellSimple size={15} weight={watching ? "fill" : "bold"} className={watching ? "text-cyan-300" : ""} />
      {watching ? "Watching" : "Watch for changes"}
    </button>
  );
}

function ContactReveal({ geid, buyerName }) {
  const navigate = useNavigate();
  const [contact, setContact] = useState(null);
  const [busy, setBusy] = useState(false);

  const reveal = async () => {
    setBusy(true);
    try {
      const res = await revealBuyerContact(geid);
      setContact(res.contact);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 402) {
        toast.error("Activate a plan to reveal verified contact details");
        navigate("/pricing");
      } else if (status === 404) {
        toast.error("No published contact is available for this buyer yet");
      } else {
        toast.error("Could not reveal contact details. Please try again.");
      }
    } finally { setBusy(false); }
  };

  const rows = contact ? [
    { icon: EnvelopeSimple, label: "Email", value: contact.email, href: contact.email ? `mailto:${contact.email}` : null },
    { icon: Phone, label: "Phone", value: contact.phone, href: contact.phone ? `tel:${contact.phone}` : null },
    { icon: Globe, label: "Website", value: contact.website, href: contact.website ? (contact.website.startsWith("http") ? contact.website : `https://${contact.website}`) : null },
    { icon: AddressBook, label: "Address", value: contact.address },
    { icon: IdentificationCard, label: "Contact person", value: contact.contact_name },
  ].filter((r) => r.value) : [];

  return (
    <div data-testid="buyer-contact-card" className="mt-6 glass-strong rounded-3xl p-6 sm:p-7 border border-cyan-400/25">
      <div className="flex items-center gap-2 mb-1">
        <AddressBook size={18} weight="fill" className="text-cyan-300" />
        <h2 className="font-display font-bold text-lg">Verified contact details</h2>
      </div>
      <p className="text-xs text-slate-500">Sourced and verified by LeadNation from official government records. Available to active members only.</p>

      {!contact ? (
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center gap-3">
          <button data-testid="reveal-contact-btn" onClick={reveal} disabled={busy}
            className="btn-primary inline-flex items-center gap-2">
            <Lock size={15} weight="bold" /> {busy ? "Revealing…" : "Reveal contact details"}
          </button>
          <span className="text-xs text-slate-500">Get {buyerName}'s verified email & phone — inside LeadNation.</span>
        </div>
      ) : (
        <div className="mt-5 grid sm:grid-cols-2 gap-3">
          {rows.map((r, i) => (
            <div key={i} data-testid={`contact-row-${r.label.toLowerCase().replace(/\s+/g, "-")}`}
              className="flex items-start gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-3.5">
              <r.icon size={18} weight="duotone" className="text-cyan-300 shrink-0 mt-0.5" />
              <div className="min-w-0">
                <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-500">{r.label}</div>
                {r.href ? (
                  <a href={r.href} target={r.label === "Website" ? "_blank" : undefined} rel="noreferrer"
                    className="text-sm text-cyan-200 hover:text-white break-all transition-colors">{r.value}</a>
                ) : (
                  <div className="text-sm text-slate-200 break-words">{r.value}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function IntelligencePanel({ intel, sources }) {
  const conf = intel.confidence || {};
  const fresh = intel.freshness || {};
  const rel = intel.source_reliability || {};
  const metrics = [
    { icon: ShieldCheck, label: "Trust Score", value: intel.trust_score ?? "—", sub: intel.trust_band || "", tone: "cyan" },
    { icon: Gauge, label: "Confidence", value: conf.label || "—", sub: conf.sources != null ? `${conf.sources} source${conf.sources === 1 ? "" : "s"}` : "", tone: "violet" },
    { icon: Clock, label: "Freshness", value: fresh.label || "—", sub: fresh.age_days != null ? `${fresh.age_days}d old` : "", tone: "emerald" },
    { icon: Certificate, label: "Source Reliability", value: rel.label || "—", sub: rel.tier ? rel.tier.toUpperCase() : "", tone: "amber" },
  ];
  const toneMap = {
    cyan: "text-cyan-300", violet: "text-violet-300", emerald: "text-emerald-300", amber: "text-amber-300",
  };
  return (
    <div data-testid="buyer-intelligence-panel" className="mt-6 glass-strong rounded-3xl p-6 sm:p-7">
      <div className="flex items-center gap-2 mb-1">
        <Sparkle size={18} weight="fill" className="text-cyan-300" />
        <h2 className="font-display font-bold text-lg">LeadNation Verified Buyer Intelligence</h2>
      </div>
      <p className="text-xs text-slate-500">Verified intelligence — never raw copied datasets.</p>

      <div className="mt-5 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {metrics.map((m, i) => (
          <div key={m.label} data-testid={`intel-metric-${i}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
            <div className="flex items-center gap-1.5 text-[10px] font-mono-display uppercase tracking-widest text-slate-400">
              <m.icon size={13} weight="fill" className={toneMap[m.tone]} /> {m.label}
            </div>
            <div className={`mt-2 font-display font-black text-2xl ${toneMap[m.tone]}`}>{m.value}</div>
            {m.sub && <div className="text-[11px] text-slate-500 mt-0.5">{m.sub}</div>}
          </div>
        ))}
      </div>

      {intel.lei_verified && (
        <div data-testid="intel-lei" className="mt-4 flex items-center gap-2 text-xs text-slate-400">
          <Fingerprint size={14} weight="fill" className="text-cyan-300" />
          <span>Globally verified company identity <span className="text-emerald-300">✓</span></span>
        </div>
      )}

      {(sources || []).length > 0 && (
        <div className="mt-5">
          <div className="flex items-center gap-1.5 text-[10px] font-mono-display uppercase tracking-widest text-slate-400 mb-2">
            <Stack size={13} weight="fill" className="text-violet-300" /> Evidence
          </div>
          <div className="flex flex-wrap gap-2">
            {sources.map((s) => (
              <span key={s} data-testid={`evidence-source-${s.replace(/\s+/g, "-").toLowerCase()}`}
                className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-200">{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PaywallGate({ reason, buyer }) {
  const { isAuthed } = useAuth();
  const navigate = useNavigate();
  const needsLogin = reason === "login" || !isAuthed;
  return (
    <div data-testid="buyer-paywall" className="mt-6 grid lg:grid-cols-3 gap-6">
      {/* Blurred teaser preview */}
      <div className="lg:col-span-2 relative glass rounded-3xl p-6 overflow-hidden">
        <div className="pointer-events-none select-none blur-[6px] opacity-60 space-y-5">
          <div>
            <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-500">Products of interest</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {(buyer.products || []).map((p) => <span key={p} className="text-sm px-3 py-1.5 rounded-full bg-white/5 text-slate-200">{p}</span>)}
            </div>
          </div>
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="flex items-center gap-3 border border-white/5 rounded-2xl p-3.5">
                <CheckCircle size={18} weight="fill" className="text-emerald-300" />
                <div className="h-3 rounded bg-white/10 flex-1" />
              </div>
            ))}
          </div>
        </div>
        <div className="absolute inset-0 grid place-items-center">
          <span className="inline-flex items-center gap-2 text-xs font-mono-display uppercase tracking-widest text-cyan-300 bg-[#050816]/70 px-4 py-2 rounded-full border border-cyan-400/25">
            <Lock size={13} weight="fill" /> Verified contact details locked
          </span>
        </div>
      </div>

      {/* CTA */}
      <div className="lg:col-span-1 glass-strong rounded-3xl p-7 border border-cyan-400/25">
        <div className="w-11 h-11 rounded-2xl grid place-items-center bg-gradient-to-br from-cyan-500/25 to-violet-500/25 border border-white/10">
          <Crown size={20} weight="duotone" className="text-cyan-300" />
        </div>
        <h2 className="mt-4 font-display font-bold text-xl">Unlock the full buyer profile</h2>
        <p className="mt-2 text-sm text-slate-400">
          {needsLogin
            ? "Sign in and activate a plan to reveal this buyer's verified contact details (email & phone), trust breakdown, products and trade corridors."
            : "Activate a plan to reveal this buyer's verified contact details (email & phone), trust breakdown, products and trade corridors."}
        </p>
        <ul className="mt-4 space-y-2 text-sm text-slate-300">
          {["Verified contact details (email & phone)", "Explainable trust score breakdown", "Products, HS families & corridors", "Request a warm introduction"].map((t) => (
            <li key={t} className="flex items-center gap-2"><CheckCircle size={15} weight="fill" className="text-emerald-300" /> {t}</li>
          ))}
        </ul>
        {needsLogin ? (
          <button data-testid="paywall-signin" onClick={() => navigate("/login")} className="btn-primary w-full justify-center mt-5">Sign in to continue</button>
        ) : (
          <button data-testid="paywall-plan" onClick={() => navigate("/pricing")} className="btn-primary w-full justify-center mt-5">View plans</button>
        )}
        {needsLogin && (
          <button onClick={() => navigate("/pricing")} className="btn-ghost w-full justify-center mt-3 text-xs">See plans & pricing</button>
        )}
      </div>
    </div>
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
