import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import CommandCenterReport from "@/components/CommandCenterReport";
import {
  User, IdentificationCard, Envelope, Phone, MapPin, Briefcase, DownloadSimple,
  Stack, UsersThree, Receipt, Gift, CrownSimple, CircleNotch, Plus, Trash, Copy,
  CheckCircle, PencilSimple, SignOut, Lightning,
} from "@phosphor-icons/react";

const SESSION_KEY = "ln_trade_session";
const getSession = () => { let s = localStorage.getItem(SESSION_KEY); if (!s) { s = crypto?.randomUUID?.() || `g-${Date.now()}`; localStorage.setItem(SESSION_KEY, s); } return s; };
const hdrs = () => ({ headers: { "X-Trade-Session": getSession() } });
const ROLES = ["Exporter", "Importer", "Manufacturer", "Supplier", "CHA / Customs Broker", "Trade Consultant", "Farmer / FPO", "Student", "Other"];
const flag = (c) => { if (!c) return "🌐"; if (c.length === 2) return c.toUpperCase().replace(/./g, (ch) => String.fromCodePoint(127397 + ch.charCodeAt(0))); return "🌐"; };
const fmtMoney = (v, cur) => { if (v == null) return "—"; try { return new Intl.NumberFormat(undefined, { style: "currency", currency: (cur || "usd").toUpperCase() }).format(v); } catch (_) { return `${v} ${cur}`; } };

const TABS = [["downloads", "Downloads", DownloadSimple], ["projects", "Projects", Stack], ["buyers", "Saved Buyers", UsersThree], ["invoices", "Invoices", Receipt], ["billing", "Billing", CrownSimple], ["referral", "Referral", Gift]];

export default function AccountPage() {
  const { account, fbUser, isAuthed, logout } = useAuth();
  const navigate = useNavigate();
  const [sp, setSp] = useSearchParams();
  const [data, setData] = useState(null);
  const [tab, setTab] = useState(sp.get("tab") || "downloads");
  const [projects, setProjects] = useState([]);
  const [buyers, setBuyers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [editing, setEditing] = useState(false);
  const [edit, setEdit] = useState({ role: "", country: "", mobile: "" });
  const [payMsg, setPayMsg] = useState("");
  const [printReport, setPrintReport] = useState(null);
  const [pricing, setPricing] = useState(null);

  const region = (data?.profile?.country || "").toUpperCase() === "IN" ? "IN" : "INTL";
  useEffect(() => { api.get("/pricing/config", { params: { region } }).then(({ data }) => setPricing(data)).catch(() => {}); }, [region]);
  const planByKey = (k) => (pricing?.plans || []).find((p) => p.key === k);

  const load = useCallback(async () => {
    const { data } = await api.get("/account/me", hdrs()); setData(data);
    setEdit({ role: data.profile.role || "", country: data.profile.country || "", mobile: data.profile.mobile || "" });
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (tab === "projects") api.get("/projects", hdrs()).then(({ data }) => setProjects(data.projects || [])); if (tab === "buyers") api.get("/account/buyers", hdrs()).then(({ data }) => setBuyers(data.buyers || [])); if (tab === "invoices") api.get("/account/invoices", hdrs()).then(({ data }) => setInvoices(data.invoices || [])); }, [tab]);

  // Complete a purchase after Stripe redirect
  useEffect(() => {
    const sid = sp.get("session_id"); const pid = sp.get("pid");
    if (!sid) return;
    (async () => {
      setPayMsg("Confirming your payment…");
      try {
        let st; for (let i = 0; i < 6; i++) { const { data } = await api.get(`/payments/status/${sid}`); st = data; if (st.status === "paid" || st.status === "expired") break; await new Promise((r) => setTimeout(r, 2000)); }
        if (st?.status === "paid") {
          if (["subscription", "monthly", "annual"].includes(st.kind)) { setPayMsg("✓ Pro pass activated — unlimited downloads!"); load(); }
          else {
            const proj = pid ? (await api.get(`/projects/${pid}`, hdrs())).data : null;
            await api.post("/downloads/record", { projectId: pid || "", projectTitle: proj?.title || "", sessionId: sid, region: st.currency === "inr" ? "IN" : "INTL" }, hdrs());
            let comp = null; if (proj?.hs || proj?.product) { try { comp = (await api.post("/command-center/compliance", { hs: proj.hs, product: proj.hs ? "" : proj.product, exporter: proj.exporter, importer: proj.importer, incoterm: proj.incoterm }, { timeout: 90000 })).data; } catch (_) {} }
            setPayMsg("✓ Payment successful — preparing your PDF…"); setPrintReport({ project: proj, compliance: comp });
            setTimeout(() => window.print(), 1200); load();
          }
        } else setPayMsg("Payment not completed. Please try again.");
      } catch (_) { setPayMsg("Could not confirm payment."); }
      setSp({ tab: "downloads" }, { replace: true });
    })();
  }, []); // eslint-disable-line

  const buyPass = async (kind = "monthly") => {
    const { data: r } = await api.post("/payments/checkout", { kind, region, origin: window.location.origin }, hdrs());
    window.location.href = r.url;
  };
  const saveProfile = async () => { await api.put("/account/profile", edit, hdrs()); setEditing(false); load(); };

  if (!data) return <div className="min-h-[60vh] flex items-center justify-center text-slate-400"><CircleNotch size={22} className="animate-spin" /></div>;
  const p = data.profile;
  const uid = (account?.user?.customer_id) || p.customerId || p.uid || getSession().slice(0, 10);
  const name = (account?.user?.full_name) || p.name || (p.guest ? "Guest Trader" : "Trader");
  const email = (account?.user?.email) || p.email || fbUser?.email || "—";

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <SEO title="My Account · LeadNation" description="Your LeadNation trade profile, downloads, projects and invoices." path="/account" />
      {printReport && <CommandCenterReport project={printReport.project} compliance={printReport.compliance} />}

      {/* Profile header (Instagram-style) */}
      <div className="glass-strong rounded-3xl p-6 sm:p-8" data-testid="account-header">
        <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center text-3xl font-display font-extrabold shrink-0" data-testid="account-avatar">
            {name.slice(0, 1).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-display font-extrabold text-2xl">{name}</h1>
              {p.role && <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-200 inline-flex items-center gap-1" data-testid="account-role-badge"><Briefcase size={12} /> {p.role}</span>}
              <span className="text-lg" title={p.country} data-testid="account-flag">{flag(p.country)} <span className="text-sm text-slate-300">{p.country || "Set country"}</span></span>
            </div>
            <div className="flex items-center gap-4 mt-2 text-sm text-slate-300 flex-wrap">
              <span className="inline-flex items-center gap-1.5" data-testid="account-uid"><IdentificationCard size={15} className="text-cyan-300" /> ID: <span className="font-mono-display text-cyan-200">{uid}</span></span>
              <span className="inline-flex items-center gap-1.5"><Envelope size={15} className="text-slate-400" /> {email}</span>
              <span className="inline-flex items-center gap-1.5"><Phone size={15} className="text-slate-400" /> {p.mobile || "—"}</span>
            </div>
            <div className="flex gap-6 mt-4">
              <Stat n={data.stats.projects} l="Projects" />
              <Stat n={data.stats.downloads} l="Downloads" />
              <Stat n={fmtMoney(data.stats.spend, invoices[0]?.currency || "usd")} l="Spend" />
              {data.subscription.active && <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-200 self-center inline-flex items-center gap-1"><CrownSimple size={12} weight="fill" /> Pass active</span>}
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <button data-testid="account-edit-btn" onClick={() => setEditing(!editing)} className="btn-ghost !py-2 !text-xs"><PencilSimple size={13} /> Edit</button>
            {isAuthed ? <button onClick={async () => { await logout(); navigate("/"); }} className="btn-ghost !py-2 !text-xs"><SignOut size={13} /> Sign out</button>
              : <Link to="/login" className="btn-primary !py-2 !text-xs">Sign in to sync</Link>}
          </div>
        </div>
        {editing && (
          <div className="mt-5 grid sm:grid-cols-3 gap-3" data-testid="account-edit-form">
            <label className="block"><span className="text-[11px] uppercase tracking-widest text-slate-400">Role</span>
              <select data-testid="account-edit-role" className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none" value={edit.role} onChange={(e) => setEdit({ ...edit, role: e.target.value })}><option value="">—</option>{ROLES.map((r) => <option key={r}>{r}</option>)}</select></label>
            <label className="block"><span className="text-[11px] uppercase tracking-widest text-slate-400">Country (ISO-2 e.g. IN, US)</span>
              <input data-testid="account-edit-country" className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none" value={edit.country} onChange={(e) => setEdit({ ...edit, country: e.target.value })} placeholder="IN" /></label>
            <label className="block"><span className="text-[11px] uppercase tracking-widest text-slate-400">Mobile</span>
              <input data-testid="account-edit-mobile" className="w-full mt-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm outline-none" value={edit.mobile} onChange={(e) => setEdit({ ...edit, mobile: e.target.value })} /></label>
            <button data-testid="account-save-profile" onClick={saveProfile} className="btn-primary !py-2 !text-sm sm:col-span-3 justify-center">Save profile</button>
          </div>
        )}
      </div>

      {payMsg && <div className="glass rounded-2xl px-4 py-3 mt-4 text-sm text-cyan-200 flex items-center gap-2" data-testid="account-pay-msg"><Lightning size={15} className="text-cyan-300" /> {payMsg}</div>}

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto mt-6 mb-4">
        {TABS.map(([k, label, I]) => (
          <button key={k} data-testid={`account-tab-${k}`} onClick={() => setTab(k)} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap transition-all ${tab === k ? "bg-cyan-500/15 text-cyan-200 border border-cyan-400/30" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
            <I size={15} weight="duotone" /> {label}
          </button>
        ))}
      </div>

      <div data-testid="account-tab-content">
        {tab === "downloads" && (data.downloads.length ? data.downloads.map((d) => (
          <div key={d.id} className="glass rounded-2xl px-4 py-3 mb-2 flex items-center gap-3 text-sm" data-testid={`account-download-${d.id}`}>
            <DownloadSimple size={16} className="text-cyan-300" /><span className="flex-1">{d.projectTitle || d.projectId}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full ${d.free ? "bg-emerald-500/15 text-emerald-300" : "bg-cyan-500/15 text-cyan-300"}`}>{d.free ? "Free" : fmtMoney(d.amount, d.currency)}</span>
            <span className="text-[11px] text-slate-500">{String(d.at).slice(0, 10)}</span>
          </div>
        )) : <Empty msg="No downloads yet. Export a Trade Intelligence Report from the Command Center." />)}

        {tab === "projects" && (projects.length ? projects.map((p) => (
          <Link to="/command-center" key={p.id} className="glass rounded-2xl px-4 py-3 mb-2 flex items-center gap-3 text-sm hover:border-cyan-400/30" data-testid={`account-project-${p.id}`}>
            <Stack size={16} className="text-cyan-300" /><span className="flex-1">{p.title}</span><span className="text-[11px] text-slate-500">{p.origin} → {p.destination} · {p.stage}</span>
          </Link>
        )) : <Empty msg="No projects yet." />)}

        {tab === "buyers" && <BuyersTab buyers={buyers} reload={() => api.get("/account/buyers", hdrs()).then(({ data }) => setBuyers(data.buyers || []))} />}

        {tab === "invoices" && (invoices.length ? invoices.map((iv, i) => (
          <div key={i} className="glass rounded-2xl px-4 py-3 mb-2 flex items-center gap-3 text-sm" data-testid={`account-invoice-${i}`}>
            <Receipt size={16} className="text-cyan-300" /><span className="flex-1 font-mono-display text-xs">{iv.number}</span><span>{iv.item}</span><span className="text-cyan-300">{fmtMoney(iv.amount, iv.currency)}</span>
          </div>
        )) : <Empty msg="No invoices yet. Paid downloads generate GST-style invoices here." />)}

        {tab === "billing" && (
          <div className="glass rounded-3xl p-6" data-testid="account-billing">
            <h3 className="font-display font-bold text-lg">Go Pro — Unlimited Reports</h3>
            <p className="text-sm text-slate-400 mt-1">Unlimited Trade Intelligence Report downloads. Your first download is always free — after that, go unlimited with a Pro plan.</p>
            {data.subscription.active ? (
              <div className="mt-4 text-emerald-300 text-sm inline-flex items-center gap-1"><CheckCircle size={16} weight="fill" /> Active until {String(data.subscription.until).slice(0, 10)}</div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-3 mt-4">
                {["monthly", "annual"].map((k) => {
                  const pl = planByKey(k);
                  if (!pl) return null;
                  const popular = (pricing?.settings?.mostPopular || "annual") === k;
                  return (
                    <div key={k} className={`rounded-2xl p-5 ${popular ? "border-2 border-cyan-400/50 bg-cyan-500/5" : "glass"}`} data-testid={`account-plan-${k}`}>
                      {popular && <div className="text-[10px] font-bold uppercase tracking-widest text-cyan-300 mb-1 inline-flex items-center gap-1"><CrownSimple size={12} weight="fill" /> Best value</div>}
                      <div className="font-display font-bold">{pl.label}</div>
                      <div className="text-3xl font-display font-extrabold text-gradient mt-1">{pl.symbol}{pl.amount}<span className="text-sm text-slate-400">/{pl.interval === "year" ? "yr" : "mo"}</span></div>
                      {k === "annual" && pricing?.annualSavingsPct ? <div className="text-[11px] text-emerald-300 mt-0.5">Save {pricing.annualSavingsPct}% vs monthly</div> : <div className="text-[11px] text-slate-500 mt-0.5">{pl.tagline}</div>}
                      <button data-testid={`account-buy-${k}`} onClick={() => buyPass(k)} className={`${popular ? "btn-primary" : "btn-ghost"} w-full justify-center mt-4`}><CrownSimple size={16} weight="bold" /> Get {pl.label}</button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {tab === "referral" && (
          <div className="glass rounded-3xl p-6" data-testid="account-referral">
            <h3 className="font-display font-bold text-lg">Refer &amp; earn</h3>
            <p className="text-sm text-slate-400 mt-1">Share your link — invite fellow traders to LeadNation.</p>
            <div className="flex items-center gap-2 mt-4">
              <input readOnly value={data.referral.link} className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm font-mono-display" data-testid="account-referral-link" />
              <button onClick={() => navigator.clipboard?.writeText(data.referral.link)} className="btn-ghost"><Copy size={15} /> Copy</button>
            </div>
            <div className="text-xs text-slate-500 mt-2">Your code: <span className="text-cyan-300 font-mono-display">{data.referral.code}</span></div>
          </div>
        )}
      </div>
    </div>
  );
}

function BuyersTab({ buyers, reload }) {
  const [f, setF] = useState({ name: "", country: "", product: "", contact: "" });
  const add = async () => { if (!f.name.trim()) return; await api.post("/account/buyers", f, hdrs()); setF({ name: "", country: "", product: "", contact: "" }); reload(); };
  return (
    <div>
      <div className="glass rounded-2xl p-4 mb-3 grid sm:grid-cols-5 gap-2" data-testid="account-buyer-form">
        <input className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm outline-none" placeholder="Buyer name" data-testid="account-buyer-name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
        <input className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm outline-none" placeholder="Country" value={f.country} onChange={(e) => setF({ ...f, country: e.target.value })} />
        <input className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm outline-none" placeholder="Product" value={f.product} onChange={(e) => setF({ ...f, product: e.target.value })} />
        <input className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm outline-none" placeholder="Contact" value={f.contact} onChange={(e) => setF({ ...f, contact: e.target.value })} />
        <button onClick={add} data-testid="account-buyer-add" className="btn-primary !py-2 !text-sm justify-center"><Plus size={14} /> Save</button>
      </div>
      {buyers.length ? buyers.map((b) => (
        <div key={b.id} className="glass rounded-2xl px-4 py-3 mb-2 flex items-center gap-3 text-sm" data-testid={`account-buyer-${b.id}`}>
          <UsersThree size={16} className="text-cyan-300" /><span className="flex-1 font-medium">{b.name}</span><span className="text-slate-400 text-xs">{b.country} · {b.product}</span>
          <button onClick={async () => { await api.delete(`/account/buyers/${b.id}`, hdrs()); reload(); }} className="text-slate-500 hover:text-rose-400"><Trash size={14} /></button>
        </div>
      )) : <Empty msg="No saved buyers yet." />}
    </div>
  );
}

const Stat = ({ n, l }) => <div><div className="font-display font-extrabold text-xl">{n}</div><div className="text-[11px] text-slate-400 uppercase tracking-wider">{l}</div></div>;
const Empty = ({ msg }) => <div className="glass rounded-2xl p-8 text-center text-slate-400 text-sm">{msg}</div>;
