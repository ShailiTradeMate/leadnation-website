import React, { useEffect, useState } from "react";
import { staffApi } from "@/lib/staffAuth";
import { X, UserPlus, Users, CheckCircle, Circle, ToggleLeft, ToggleRight, PaperPlaneTilt } from "@phosphor-icons/react";

export default function AllocatePanel({ onClose, onAllocated }) {
  const [subs, setSubs] = useState([]);
  const [pending, setPending] = useState({ pending: 0, unassigned: 0 });
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const [s, p] = await Promise.all([
        staffApi.get("/admin/subadmins"),
        staffApi.get("/admin/allocate/pending"),
      ]);
      setSubs(s.data.subadmins || []);
      setPending(p.data || { pending: 0, unassigned: 0 });
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not load sub-admins.");
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const activeSubs = subs.filter((s) => s.active);
  const toggleSel = (id) => setSelected((p) => ({ ...p, [id]: !p[id] }));

  const allocate = async () => {
    const ids = Object.keys(selected).filter((k) => selected[k]);
    if (ids.length === 0) { setErr("Select at least one active sub-admin."); return; }
    setBusy("allocate"); setErr(""); setMsg("");
    try {
      const { data } = await staffApi.post("/admin/allocate", { subadmin_ids: ids });
      if (data.allocated === 0) { setMsg(data.message || "No pending requests to allocate."); }
      else {
        const dist = Object.entries(data.distribution || {}).map(([n, c]) => `${n}: ${c}`).join(", ");
        setMsg(`Allocated ${data.allocated} request(s) — ${dist}. Notification emails sent.`);
      }
      await load();
      onAllocated && onAllocated();
    } catch (e) { setErr(e?.response?.data?.detail || "Allocation failed."); }
    finally { setBusy(""); }
  };

  const createSub = async (e) => {
    e.preventDefault();
    setBusy("create"); setErr(""); setMsg("");
    try {
      await staffApi.post("/admin/subadmins", form);
      setMsg(`Sub-admin ${form.email} created.`);
      setForm({ name: "", email: "", password: "" });
      await load();
    } catch (e2) { setErr(e2?.response?.data?.detail || "Could not create sub-admin."); }
    finally { setBusy(""); }
  };

  const toggleActive = async (s) => {
    setBusy(`toggle-${s.id}`); setErr("");
    try {
      await staffApi.patch(`/admin/subadmins/${s.id}`, { active: !s.active });
      await load();
    } catch (e) { setErr(e?.response?.data?.detail || "Update failed."); }
    finally { setBusy(""); }
  };

  return (
    <div className="fixed inset-0 z-[200] grid place-items-center p-4 bg-black/70 backdrop-blur-sm" data-testid="allocate-panel">
      <div className="glass-strong rounded-3xl w-full max-w-3xl max-h-[88vh] overflow-auto p-6 sm:p-8 relative">
        <button onClick={onClose} data-testid="allocate-close" className="absolute right-5 top-5 text-slate-400 hover:text-white"><X size={20} /></button>
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Main Admin</div>
        <h2 className="font-display font-extrabold text-2xl mt-1">Allocate & manage sub-admins</h2>

        {err && <div data-testid="allocate-error" className="mt-3 text-sm text-rose-300 bg-rose-500/10 rounded-xl p-3">{err}</div>}
        {msg && <div data-testid="allocate-msg" className="mt-3 text-sm text-emerald-300 bg-emerald-500/10 rounded-xl p-3">{msg}</div>}

        {/* Function 1 — Allocate */}
        <div className="mt-6">
          <div className="flex items-center gap-2 text-sm font-semibold"><Users size={16} className="text-cyan-300" /> Allocate pending reviews</div>
          <p className="text-xs text-slate-400 mt-1">
            <b className="text-slate-200">{pending.unassigned}</b> unassigned of <b className="text-slate-200">{pending.pending}</b> pending. Select sub-admins to distribute them evenly.
          </p>
          <div className="mt-3 space-y-2">
            {activeSubs.length === 0 && !loading && <div className="text-sm text-slate-400">No active sub-admins. Create one below.</div>}
            {activeSubs.map((s) => (
              <button key={s.id} type="button" data-testid={`allocate-select-${s.id}`} onClick={() => toggleSel(s.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border text-left ${selected[s.id] ? "border-cyan-400/50 bg-cyan-400/10" : "border-white/10 bg-white/5"}`}>
                <span className="flex items-center gap-3">
                  {selected[s.id] ? <CheckCircle size={18} weight="fill" className="text-cyan-300" /> : <Circle size={18} className="text-slate-500" />}
                  <span>
                    <span className="text-sm font-medium">{s.name}</span>
                    <span className="text-xs text-slate-400 ml-2">{s.email}</span>
                  </span>
                </span>
                <span className="text-[11px] text-slate-400">{s.assigned_pending} in queue</span>
              </button>
            ))}
          </div>
          <button data-testid="allocate-submit" onClick={allocate} disabled={busy === "allocate"}
            className="btn-primary mt-4 justify-center disabled:opacity-50">
            <PaperPlaneTilt size={15} /> {busy === "allocate" ? "Allocating…" : "Allocate & notify"}
          </button>
        </div>

        <div className="h-px bg-white/10 my-7" />

        {/* Function 2 — Manage access */}
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold"><UserPlus size={16} className="text-cyan-300" /> Create sub-admin</div>
          <form onSubmit={createSub} className="mt-3 grid sm:grid-cols-3 gap-3">
            <input data-testid="subadmin-name" required placeholder="Name" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} className="glass rounded-xl px-3 py-2.5 text-sm outline-none" />
            <input data-testid="subadmin-email" required type="email" placeholder="Email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} className="glass rounded-xl px-3 py-2.5 text-sm outline-none" />
            <input data-testid="subadmin-password" required type="text" placeholder="Password (min 6)" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} className="glass rounded-xl px-3 py-2.5 text-sm outline-none" />
            <button data-testid="subadmin-create" disabled={busy === "create"} className="btn-ghost sm:col-span-3 justify-center disabled:opacity-50">
              {busy === "create" ? "Creating…" : "Create sub-admin account"}
            </button>
          </form>

          <div className="mt-5 space-y-2">
            <div className="text-xs uppercase tracking-widest text-slate-500">All sub-admins</div>
            {subs.map((s) => (
              <div key={s.id} data-testid={`subadmin-row-${s.id}`} className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                <div>
                  <span className="text-sm font-medium">{s.name}</span>
                  <span className="text-xs text-slate-400 ml-2">{s.email}</span>
                  <span className={`text-[10px] uppercase ml-2 px-2 py-0.5 rounded-full ${s.active ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-500/20 text-slate-400"}`}>
                    {s.active ? "Active" : "Inactive"}
                  </span>
                </div>
                <button data-testid={`subadmin-toggle-${s.id}`} onClick={() => toggleActive(s)} disabled={busy === `toggle-${s.id}`}
                  className="text-slate-300 hover:text-white flex items-center gap-1.5 text-xs">
                  {s.active ? <ToggleRight size={22} weight="fill" className="text-emerald-400" /> : <ToggleLeft size={22} className="text-slate-500" />}
                  {s.active ? "Deactivate" : "Activate"}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
