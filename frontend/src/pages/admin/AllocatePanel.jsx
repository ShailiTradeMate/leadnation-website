import React, { useEffect, useMemo, useState } from "react";
import { staffApi } from "@/lib/staffAuth";
import { X, UserPlus, Users, CheckCircle, Circle, ToggleLeft, ToggleRight, PaperPlaneTilt, Prohibit, WarningCircle } from "@phosphor-icons/react";

export default function AllocatePanel({ onClose, onAllocated }) {
  const [subs, setSubs] = useState([]);
  const [cats, setCats] = useState([]);
  const [catKey, setCatKey] = useState("pending_unassigned");
  const [picked, setPicked] = useState({}); // submission_id -> bool
  const [selected, setSelected] = useState({}); // subadmin id -> bool
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const [s, c] = await Promise.all([
        staffApi.get("/admin/subadmins"),
        staffApi.get("/admin/allocate/categories"),
      ]);
      setSubs(s.data.subadmins || []);
      setCats(c.data.categories || []);
      setPicked({});
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not load allocation data.");
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const activeSubs = subs.filter((s) => s.active);
  const cat = useMemo(() => cats.find((c) => c.key === catKey) || null, [cats, catKey]);
  const items = cat?.items || [];
  const pickedIds = useMemo(() => Object.keys(picked).filter((k) => picked[k]), [picked]);

  const toggleSel = (id) => setSelected((p) => ({ ...p, [id]: !p[id] }));
  const togglePick = (id) => setPicked((p) => ({ ...p, [id]: !p[id] }));
  const pickAll = () => {
    const all = {};
    items.forEach((i) => { if (i.submission_id) all[i.submission_id] = true; });
    setPicked(all);
  };

  const allocate = async () => {
    const ids = Object.keys(selected).filter((k) => selected[k]);
    if (!cat?.allocatable) { setErr("This category cannot be allocated for review."); return; }
    if (ids.length === 0) { setErr("Select at least one active sub-admin."); return; }
    if (pickedIds.length === 0) { setErr("Select at least one user to allocate."); return; }
    setBusy("allocate"); setErr(""); setMsg("");
    try {
      const { data } = await staffApi.post("/admin/allocate", {
        subadmin_ids: ids, submission_ids: pickedIds, category: catKey,
      });
      if (data.allocated === 0) setMsg(data.message || "No pending requests to allocate.");
      else {
        const dist = Object.entries(data.distribution || {}).map(([n, c2]) => `${n}: ${c2}`).join(", ");
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
      <div className="glass-strong rounded-3xl w-full max-w-4xl max-h-[88vh] overflow-auto p-6 sm:p-8 relative">
        <button onClick={onClose} data-testid="allocate-close" className="absolute right-5 top-5 text-slate-400 hover:text-white"><X size={20} /></button>
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Main Admin</div>
        <h2 className="font-display font-extrabold text-2xl mt-1">Allocate & manage sub-admins</h2>

        {err && <div data-testid="allocate-error" className="mt-3 text-sm text-rose-300 bg-rose-500/10 rounded-xl p-3">{err}</div>}
        {msg && <div data-testid="allocate-msg" className="mt-3 text-sm text-emerald-300 bg-emerald-500/10 rounded-xl p-3">{msg}</div>}

        {/* Step 1 — Category */}
        <div className="mt-6">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Users size={16} className="text-cyan-300" /> 1. Choose a category
          </div>
          <div className="mt-3 flex flex-wrap gap-2" data-testid="allocate-categories">
            {cats.map((c) => (
              <button key={c.key} type="button" data-testid={`allocate-cat-${c.key}`}
                onClick={() => { setCatKey(c.key); setPicked({}); setErr(""); setMsg(""); }}
                className={`px-3 py-2 rounded-xl border text-xs flex items-center gap-2 ${catKey === c.key ? "border-cyan-400/60 bg-cyan-400/10 text-white" : "border-white/10 bg-white/5 text-slate-300"}`}>
                {!c.allocatable && <Prohibit size={13} className="text-rose-300" />}
                {c.label}
                <span className="font-mono-display text-cyan-300">{c.count}</span>
              </button>
            ))}
          </div>
          {cat && <p className="text-xs text-slate-400 mt-2" data-testid="allocate-hint">{cat.hint}</p>}
        </div>

        {/* Step 2 — Candidates */}
        <div className="mt-6">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">2. Select users {cat?.allocatable ? "" : "(view only)"}</div>
            {cat?.allocatable && items.length > 0 && (
              <button type="button" data-testid="allocate-pick-all" onClick={pickAll} className="text-xs text-cyan-300 hover:underline">Select all {items.length}</button>
            )}
          </div>
          {!cat?.allocatable && (
            <div className="mt-2 text-xs text-rose-300 bg-rose-500/10 rounded-xl p-3" data-testid="allocate-blocked-note">
              Users in this category cannot be allocated for verification review.
            </div>
          )}
          <div className="mt-3 max-h-64 overflow-auto rounded-xl border border-white/10 divide-y divide-white/5" data-testid="allocate-candidates">
            {loading && <div className="p-4 text-sm text-slate-400">Loading…</div>}
            {!loading && items.length === 0 && <div className="p-4 text-sm text-slate-400" data-testid="allocate-empty">No users in this category.</div>}
            {items.map((i) => {
              const on = Boolean(picked[i.submission_id]);
              const clickable = cat?.allocatable && i.submission_id;
              return (
                <button key={i.submission_id || i.uid} type="button" disabled={!clickable}
                  data-testid={`allocate-user-${i.submission_id || i.uid}`}
                  onClick={() => clickable && togglePick(i.submission_id)}
                  className={`w-full text-left px-4 py-3 flex items-start justify-between gap-3 ${on ? "bg-cyan-400/10" : "bg-white/[0.02]"} ${clickable ? "hover:bg-white/[0.06]" : "opacity-70 cursor-not-allowed"}`}>
                  <span className="flex items-start gap-3 min-w-0">
                    {clickable && (on ? <CheckCircle size={17} weight="fill" className="text-cyan-300 mt-0.5" /> : <Circle size={17} className="text-slate-500 mt-0.5" />)}
                    <span className="min-w-0">
                      <span className="text-sm font-medium">{i.name || i.email || "—"}</span>
                      <span className="text-xs text-slate-400 ml-2">{i.email || "—"}</span>
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {i.customer_id ? `ID ${i.customer_id} · ` : ""}{i.company_name || "No company"} · {i.mobile || "No contact number"}
                      </div>
                      {i.missing?.length > 0 && (
                        <div className="text-[11px] text-amber-300 mt-1 flex items-center gap-1">
                          <WarningCircle size={12} /> Missing: {i.missing.join(", ")}
                        </div>
                      )}
                    </span>
                  </span>
                  <span className="text-[10px] uppercase text-slate-400 shrink-0">
                    {i.assigned_to_name ? `→ ${i.assigned_to_name}` : (i.status || "").replace(/_/g, " ")}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 3 — Sub-admins */}
        <div className="mt-6">
          <div className="text-sm font-semibold">3. Distribute to sub-admins</div>
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
          <button data-testid="allocate-submit" onClick={allocate}
            disabled={busy === "allocate" || !cat?.allocatable || pickedIds.length === 0}
            className="btn-primary mt-4 justify-center disabled:opacity-50">
            <PaperPlaneTilt size={15} /> {busy === "allocate" ? "Allocating…" : `Allocate ${pickedIds.length || ""} & notify`}
          </button>
        </div>

        <div className="h-px bg-white/10 my-7" />

        {/* Manage access */}
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
