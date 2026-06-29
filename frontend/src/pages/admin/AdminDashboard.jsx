import React, { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { adminApi, adminLogin, isAdminLoggedIn, setAdminToken, getAdminToken } from "@/lib/admin";
import { API } from "@/lib/api";
import {
  Database, UserList, Users, Briefcase, ChartBar, SignOut, FloppyDisk, TrashSimple, Plus, X, FileCsv, Eye, Brain, SlidersHorizontal,
} from "@phosphor-icons/react";
import { useSettings } from "@/lib/SettingsContext";

const COLLECTIONS = ["countries", "products", "corridors", "hsn_codes", "industries", "blog"];

export function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  if (isAdminLoggedIn()) return <Navigate to="/admin-cms" replace />;

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr(""); setLoading(true);
    try { await adminLogin(username.trim(), password); navigate("/admin-cms"); }
    catch (_) { setErr("Invalid username or password"); }
    finally { setLoading(false); }
  };

  return (
    <section className="min-h-[80vh] grid place-items-center px-6">
      <form onSubmit={onSubmit} data-testid="admin-login-form" className="glass-strong rounded-3xl p-8 w-full max-w-md">
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Admin Control Center</div>
        <h1 className="font-display font-extrabold text-3xl mt-2">Sign in to LeadNation</h1>
        <p className="text-slate-400 text-sm mt-2">Secure access to the CMS, leads, services, Brain and site controls.</p>
        <input
          data-testid="admin-login-username"
          autoFocus type="text" autoComplete="username"
          value={username} onChange={(e) => setUsername(e.target.value)}
          placeholder="Admin ID"
          className="mt-5 w-full glass rounded-xl px-4 py-3 outline-none"
        />
        <input
          data-testid="admin-login-password"
          type="password" autoComplete="current-password"
          value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="mt-3 w-full glass rounded-xl px-4 py-3 outline-none"
        />
        {err && <div data-testid="admin-login-error" className="text-rose-300 text-sm mt-2">{err}</div>}
        <button data-testid="admin-login-submit" disabled={loading} className="btn-primary w-full justify-center mt-4 disabled:opacity-50">{loading ? "Signing in…" : "Sign in"}</button>
      </form>
    </section>
  );
}

export default function AdminDashboard() {
  const [tab, setTab] = useState("dashboard");
  const [stats, setStats] = useState([]);
  const navigate = useNavigate();
  useEffect(() => {
    if (!isAdminLoggedIn()) { navigate("/admin-login"); return; }
    adminApi.get("/admin/collections").then((r) => setStats(r.data)).catch(() => navigate("/admin-login"));
  }, [navigate]);

  const logout = () => { setAdminToken(""); navigate("/admin-login"); };

  return (
    <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-24">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Admin Console</div>
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-2">LeadNation CMS</h1>
        </div>
        <button data-testid="admin-logout" onClick={logout} className="btn-ghost !py-2 text-xs"><SignOut size={14} weight="bold" /> Logout</button>
      </div>

      <div className="mt-8 glass-strong rounded-2xl p-2 flex gap-1 overflow-auto">
        {[
          { k: "dashboard", l: "Dashboard", I: ChartBar },
          { k: "cms", l: "Content", I: Database },
          { k: "leads", l: "Leads", I: UserList },
          { k: "service-requests", l: "Service Requests", I: Briefcase },
          { k: "events", l: "Events", I: Eye },
          { k: "control-center", l: "Control Center", I: SlidersHorizontal },
        ].map((t) => (
          <button key={t.k} data-testid={`admin-tab-${t.k}`} onClick={() => setTab(t.k)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap ${tab === t.k ? "tab-active text-white" : "text-slate-300 hover:bg-white/5"}`}>
            <t.I size={14} weight="duotone" />{t.l}
          </button>
        ))}
        <button data-testid="admin-tab-brain" onClick={() => navigate("/admin/brain")}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap text-violet-200 hover:bg-violet-500/10 border border-violet-400/20">
          <Brain size={14} weight="duotone" />Brain
        </button>
      </div>

      <div className="mt-6">
        {tab === "dashboard" && <Stats stats={stats} />}
        {tab === "cms" && <CmsManager />}
        {tab === "leads" && <Leads />}
        {tab === "service-requests" && <ServiceRequests />}
        {tab === "events" && <Events />}
        {tab === "control-center" && <ControlCenter />}
      </div>
    </section>
  );
}

function Stats({ stats }) {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((s) => (
        <div key={s.name} data-testid={`admin-stat-${s.name}`} className="glass rounded-3xl p-6">
          <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{s.name.replace(/_/g, " ")}</div>
          <div className="mt-2 text-4xl font-display font-extrabold gradient-text">{s.count}</div>
        </div>
      ))}
    </div>
  );
}

function CmsManager() {
  const [coll, setColl] = useState(COLLECTIONS[0]);
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null); // {id?, json}
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const reload = async () => {
    setLoading(true);
    try {
      const { data } = await adminApi.get(`/admin/collection/${coll}`);
      setItems(data);
    } finally { setLoading(false); }
  };
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [coll]);

  const startCreate = () => setEditing({ json: JSON.stringify({ slug: "", name: "", published: true }, null, 2) });
  const startEdit = (it) => setEditing({ id: it.id, json: JSON.stringify(it, null, 2) });

  const save = async () => {
    setErr("");
    let payload;
    try { payload = JSON.parse(editing.json); }
    catch (e) { setErr("Invalid JSON"); return; }
    try {
      if (editing.id) await adminApi.put(`/admin/collection/${coll}/${editing.id}`, payload);
      else await adminApi.post(`/admin/collection/${coll}`, payload);
      setEditing(null); await reload();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed");
    }
  };
  const del = async (id) => {
    if (!window.confirm("Delete this item?")) return;
    await adminApi.delete(`/admin/collection/${coll}/${id}`); await reload();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 flex-wrap">
        {COLLECTIONS.map((c) => (
          <button key={c} data-testid={`admin-coll-${c}`} onClick={() => setColl(c)}
            className={`px-3 py-1.5 rounded-full text-xs font-mono-display tracking-widest uppercase ${coll === c ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>
            {c.replace(/_/g, " ")}
          </button>
        ))}
        <button data-testid="admin-new-item" onClick={startCreate} className="btn-primary !py-2 !px-4 text-xs ml-auto"><Plus size={14} weight="bold" /> New item</button>
      </div>

      {loading ? <div className="text-slate-400">Loading…</div> : (
        <div className="glass-strong rounded-3xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
              <tr><th className="text-left px-4 py-3">Slug / Key</th><th className="text-left px-4 py-3">Title</th><th className="text-left px-4 py-3">Published</th><th className="text-right px-4 py-3">Actions</th></tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-t border-white/5">
                  <td className="px-4 py-3 font-mono-display text-xs">{it.slug || it.code}</td>
                  <td className="px-4 py-3">{it.name || it.title}</td>
                  <td className="px-4 py-3 text-xs">{it.published === false ? <span className="text-amber-300">Draft</span> : <span className="text-emerald-300">Live</span>}</td>
                  <td className="px-4 py-3 text-right">
                    <button data-testid={`admin-edit-${it.id}`} onClick={() => startEdit(it)} className="text-cyan-300 hover:underline text-xs mr-3">Edit</button>
                    <button data-testid={`admin-delete-${it.id}`} onClick={() => del(it.id)} className="text-rose-300 hover:underline text-xs">Delete</button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">No items yet.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur grid place-items-center p-6">
          <div className="glass-strong rounded-3xl p-6 w-full max-w-2xl">
            <div className="flex items-center justify-between">
              <div className="font-display font-bold text-xl">{editing.id ? "Edit item" : "New item"}</div>
              <button onClick={() => setEditing(null)} className="text-slate-400 hover:text-white"><X size={18} /></button>
            </div>
            <p className="text-xs text-slate-400 mt-1">Edit raw JSON — slug, name and any fields are fully customisable.</p>
            <textarea
              data-testid="admin-editor"
              value={editing.json}
              onChange={(e) => setEditing({ ...editing, json: e.target.value })}
              spellCheck={false}
              rows={18}
              className="w-full glass rounded-xl px-4 py-3 outline-none font-mono-display text-xs mt-3"
            />
            {err && <div className="text-rose-300 text-sm mt-2">{err}</div>}
            <div className="mt-3 flex gap-3 justify-end">
              <button onClick={() => setEditing(null)} className="btn-ghost !py-2 text-xs">Cancel</button>
              <button data-testid="admin-save" onClick={save} className="btn-primary !py-2 text-xs"><FloppyDisk size={14} weight="bold" /> Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Leads() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  useEffect(() => { adminApi.get("/admin/leads").then((r) => setItems(r.data)); }, []);
  const filtered = useMemo(() => {
    const ql = q.toLowerCase();
    if (!ql) return items;
    return items.filter((i) => Object.values(i).some((v) => typeof v === "string" && v.toLowerCase().includes(ql)));
  }, [items, q]);
  const csvHref = `${API}/admin/leads.csv?token=${encodeURIComponent(getAdminToken())}`;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <input data-testid="admin-leads-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search leads…" className="glass rounded-xl px-4 py-3 outline-none w-72" />
        <a data-testid="admin-leads-csv" href={csvHref} download className="btn-primary !py-2 text-xs ml-auto"><FileCsv size={14} weight="bold" /> Export CSV</a>
      </div>
      <div className="glass-strong rounded-3xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
            <tr>
              <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Source</th><th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3">Email</th><th className="text-left px-4 py-3">Phone</th><th className="text-left px-4 py-3">Country</th>
              <th className="text-left px-4 py-3">Message</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((it) => (
              <tr key={it.id} className="border-t border-white/5">
                <td className="px-4 py-3 text-xs text-slate-400">{(it.createdAt || "").slice(0, 16).replace("T", " ")}</td>
                <td className="px-4 py-3 text-xs text-cyan-300 font-mono-display">{it.source || "-"}</td>
                <td className="px-4 py-3">{it.name || "-"}</td>
                <td className="px-4 py-3 text-xs">{it.email || "-"}</td>
                <td className="px-4 py-3 text-xs">{it.phone || "-"}</td>
                <td className="px-4 py-3 text-xs">{it.country || "-"}</td>
                <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate">{it.message || "-"}</td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">No leads yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ServiceRequests() {
  const [items, setItems] = useState([]);
  const reload = () => adminApi.get("/admin/service-requests").then((r) => setItems(r.data));
  useEffect(() => { reload(); }, []);

  const updateStatus = async (id, status) => {
    await adminApi.put(`/admin/service-requests/${id}`, { status });
    reload();
  };
  const assign = async (id, ca) => {
    await adminApi.put(`/admin/service-requests/${id}`, { assignedCa: ca });
    reload();
  };

  return (
    <div className="glass-strong rounded-3xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
          <tr>
            <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Service</th>
            <th className="text-left px-4 py-3">Name</th><th className="text-left px-4 py-3">Email / Phone</th>
            <th className="text-left px-4 py-3">Status</th><th className="text-left px-4 py-3">Assigned CA</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-t border-white/5">
              <td className="px-4 py-3 text-xs text-slate-400">{(it.createdAt || "").slice(0, 16).replace("T", " ")}</td>
              <td className="px-4 py-3 text-xs text-cyan-300 font-mono-display">{it.service}</td>
              <td className="px-4 py-3">{it.name}</td>
              <td className="px-4 py-3 text-xs"><div>{it.email}</div><div className="text-slate-500">{it.phone}</div></td>
              <td className="px-4 py-3">
                <select data-testid={`admin-sr-status-${it.id}`} value={it.status || "new"} onChange={(e) => updateStatus(it.id, e.target.value)} className="glass rounded-lg px-2 py-1 text-xs">
                  {["new", "assigned", "in-progress", "completed", "cancelled"].map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
                </select>
              </td>
              <td className="px-4 py-3">
                <input data-testid={`admin-sr-ca-${it.id}`} defaultValue={it.assignedCa || ""} onBlur={(e) => e.target.value !== (it.assignedCa || "") && assign(it.id, e.target.value)} placeholder="CA name" className="glass rounded-lg px-2 py-1 text-xs w-40" />
              </td>
            </tr>
          ))}
          {items.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No service requests yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function Events() {
  const [items, setItems] = useState([]);
  useEffect(() => { adminApi.get("/admin/events").then((r) => setItems(r.data)); }, []);
  return (
    <div className="glass-strong rounded-3xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
          <tr><th className="text-left px-4 py-3">When</th><th className="text-left px-4 py-3">Event</th><th className="text-left px-4 py-3">Path</th><th className="text-left px-4 py-3">Meta</th></tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-t border-white/5">
              <td className="px-4 py-3 text-xs text-slate-400">{(it.createdAt || "").slice(0, 19).replace("T", " ")}</td>
              <td className="px-4 py-3 text-xs text-cyan-300">{it.name}</td>
              <td className="px-4 py-3 text-xs">{it.path}</td>
              <td className="px-4 py-3 text-[10px] text-slate-500 max-w-md truncate">{JSON.stringify(it.meta || {})}</td>
            </tr>
          ))}
          {items.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">No events tracked yet — interact with the website to generate events.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}


const FEATURE_LABELS = {
  tools: "Tools Hub", services: "Business Services", brain: "LeadNation Brain",
  customs: "Customs & Compliance", intelligence: "Intelligence", expo: "Expos & Events",
  academy: "Academy", blog: "Blog", trade_news: "Trade News",
};

function ControlCenter() {
  const { refresh } = useSettings();
  const [form, setForm] = useState(null);
  const [services, setServices] = useState([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [pwd, setPwd] = useState("");
  const [pwdMsg, setPwdMsg] = useState("");
  const [dutyMeta, setDutyMeta] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    adminApi.get("/settings").then((r) => setForm({
      accentColor: r.data.accentColor || "#00C2FF",
      maintenance: !!r.data.maintenance,
      maintenanceMessage: r.data.maintenanceMessage || "",
      features: r.data.features || {},
      serviceRates: r.data.serviceRates || {},
    }));
    adminApi.get("/services").then((r) => setServices(r.data)).catch(() => {});
    adminApi.get("/duty/meta").then((r) => setDutyMeta(r.data)).catch(() => {});
  }, []);

  const refreshData = async () => {
    setRefreshing(true);
    try { const { data } = await adminApi.post("/duty/refresh"); setDutyMeta(data); }
    catch (_) {}
    finally { setRefreshing(false); }
  };

  if (!form) return <div className="text-slate-400">Loading…</div>;

  const setF = (patch) => setForm((p) => ({ ...p, ...patch }));
  const toggleFeature = (k) => setF({ features: { ...form.features, [k]: !(form.features[k] !== false) } });
  const setRate = (slug, val) => setF({ serviceRates: { ...form.serviceRates, [slug]: val } });

  const save = async () => {
    setSaving(true); setMsg("");
    try {
      const rates = Object.fromEntries(Object.entries(form.serviceRates).filter(([, v]) => v && v.trim()));
      await adminApi.put("/admin/settings", {
        accentColor: form.accentColor,
        maintenance: form.maintenance,
        maintenanceMessage: form.maintenanceMessage,
        features: form.features,
        serviceRates: rates,
      });
      await refresh();
      setMsg("Saved — changes are live across the site.");
    } catch (e) {
      setMsg(e?.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  const changePassword = async () => {
    setPwdMsg("");
    if (pwd.length < 6) { setPwdMsg("Password must be at least 6 characters"); return; }
    try { await adminApi.post("/auth/admin/password", { newPassword: pwd }); setPwd(""); setPwdMsg("Password updated."); }
    catch (e) { setPwdMsg(e?.response?.data?.detail || "Failed"); }
  };

  const PRESETS = ["#00C2FF", "#7C3AED", "#10B981", "#F59E0B", "#EF4444", "#EC4899"];

  return (
    <div className="space-y-6" data-testid="control-center">
      <div className="glass-strong rounded-3xl p-6 space-y-4">
        <div className="font-display font-bold text-xl flex items-center gap-2"><SlidersHorizontal size={18} weight="duotone" className="text-cyan-300" /> Site Branding</div>
        <div>
          <div className="text-[11px] font-mono-display tracking-widest uppercase text-slate-400 mb-2">Accent colour (live)</div>
          <div className="flex items-center gap-3 flex-wrap">
            <input data-testid="cc-accent-color" type="color" value={form.accentColor} onChange={(e) => setF({ accentColor: e.target.value })} className="w-12 h-12 rounded-xl bg-transparent border border-white/10 cursor-pointer" />
            <input data-testid="cc-accent-hex" value={form.accentColor} onChange={(e) => setF({ accentColor: e.target.value })} className="glass rounded-xl px-3 py-2 w-32 font-mono-display text-sm" />
            {PRESETS.map((c) => (
              <button key={c} data-testid={`cc-preset-${c}`} onClick={() => setF({ accentColor: c })} className="w-8 h-8 rounded-full border border-white/20" style={{ background: c }} aria-label={c} />
            ))}
          </div>
        </div>
      </div>

      <div className="glass-strong rounded-3xl p-6 space-y-4">
        <div className="font-display font-bold text-xl">Maintenance Mode</div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input data-testid="cc-maintenance-toggle" type="checkbox" checked={form.maintenance} onChange={(e) => setF({ maintenance: e.target.checked })} className="w-5 h-5 accent-cyan-400" />
          <span className="text-sm text-slate-300">Take the public site offline (admin stays accessible)</span>
        </label>
        <input data-testid="cc-maintenance-message" value={form.maintenanceMessage} onChange={(e) => setF({ maintenanceMessage: e.target.value })} placeholder="Maintenance message" className="w-full glass rounded-xl px-4 py-3 outline-none text-sm" />
      </div>

      <div className="glass-strong rounded-3xl p-6">
        <div className="font-display font-bold text-xl mb-4">Feature Toggles</div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.keys(FEATURE_LABELS).map((k) => {
            const on = form.features[k] !== false;
            return (
              <button key={k} data-testid={`cc-feature-${k}`} onClick={() => toggleFeature(k)}
                className={`flex items-center justify-between glass rounded-xl px-4 py-3 text-sm transition-all ${on ? "border-cyan-400/40" : "opacity-60"}`}>
                <span>{FEATURE_LABELS[k]}</span>
                <span className={`text-[10px] font-mono-display uppercase px-2 py-0.5 rounded-full ${on ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>{on ? "On" : "Off"}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="glass-strong rounded-3xl p-6">
        <div className="font-display font-bold text-xl mb-1">Service Rate Overrides</div>
        <p className="text-xs text-slate-400 mb-4">Override the "from" price shown on service pages. Leave blank to use the default.</p>
        <div className="space-y-2">
          {services.map((s) => (
            <div key={s.slug} className="flex items-center gap-3 flex-wrap">
              <div className="flex-1 min-w-[180px]">
                <div className="text-sm font-medium">{s.name}</div>
                <div className="text-[11px] text-slate-500 font-mono-display">{s.slug} · default {s.priceFrom}</div>
              </div>
              <input data-testid={`cc-rate-${s.slug}`} value={form.serviceRates[s.slug] || ""} onChange={(e) => setRate(s.slug, e.target.value)} placeholder={s.priceFrom} className="glass rounded-xl px-3 py-2 w-48 text-sm" />
            </div>
          ))}
          {services.length === 0 && <div className="text-slate-500 text-sm">No services found.</div>}
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <button data-testid="cc-save" onClick={save} disabled={saving} className="btn-primary disabled:opacity-50"><FloppyDisk size={16} weight="bold" /> {saving ? "Saving…" : "Save changes"}</button>
        {msg && <span data-testid="cc-save-msg" className="text-sm text-emerald-300">{msg}</span>}
      </div>

      <div className="glass-strong rounded-3xl p-6 space-y-3" data-testid="cc-data-refresh">
        <div className="font-display font-bold text-xl">Trade & Duty Data</div>
        <p className="text-xs text-slate-400">Global tariffs (WITS), trade stats (OEC/Comtrade) and RoDTEP refresh automatically every 7 days. You can force a refresh now.</p>
        <div className="flex items-center gap-3 flex-wrap">
          <button data-testid="cc-refresh-data" onClick={refreshData} disabled={refreshing} className="btn-ghost !py-2.5 text-sm disabled:opacity-50">{refreshing ? "Refreshing…" : "Refresh data now"}</button>
          {dutyMeta && <span className="text-sm text-slate-400">Last refreshed: <span className="text-cyan-300">{String(dutyMeta.lastRefresh).slice(0, 16).replace("T", " ")} UTC</span></span>}
        </div>
      </div>

      <div className="glass-strong rounded-3xl p-6 space-y-3">
        <div className="font-display font-bold text-xl">Change Admin Password</div>
        <div className="flex items-center gap-3 flex-wrap">
          <input data-testid="cc-new-password" type="password" value={pwd} onChange={(e) => setPwd(e.target.value)} placeholder="New password" className="glass rounded-xl px-4 py-3 w-64 outline-none" />
          <button data-testid="cc-change-password" onClick={changePassword} className="btn-ghost !py-2.5 text-sm">Update password</button>
          {pwdMsg && <span className="text-sm text-cyan-300">{pwdMsg}</span>}
        </div>
      </div>
    </div>
  );
}
