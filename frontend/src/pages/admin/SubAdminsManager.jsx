import React, { useEffect, useState } from "react";
import { staffApi } from "@/lib/staffAuth";
import { toast } from "sonner";
import { UserPlus, ToggleLeft, ToggleRight, Briefcase, IdentificationBadge, PencilSimple } from "@phosphor-icons/react";
import SubAdminEditModal from "@/pages/admin/SubAdminEditModal";

const CATS = ["CA", "Associate"];
const catStyle = (c) => c === "CA" ? "bg-cyan-500/20 text-cyan-200 border-cyan-400/40" : c === "Associate" ? "bg-violet-500/20 text-violet-200 border-violet-400/40" : "bg-amber-400/15 text-amber-200 border-amber-400/40";

export default function SubAdminsManager() {
  const [subs, setSubs] = useState([]);
  const [form, setForm] = useState({ name: "", email: "", password: "", category: "CA" });
  const [busy, setBusy] = useState("");
  const [editing, setEditing] = useState(null);
  const load = () => staffApi.get("/admin/subadmins").then((r) => setSubs(r.data.subadmins || [])).catch(() => toast.error("Could not load sub-admins"));
  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setBusy("create");
    try {
      await staffApi.post("/admin/subadmins", form);
      toast.success(`${form.category} account created for ${form.email}`);
      setForm({ name: "", email: "", password: "", category: "CA" });
      load();
    } catch (err) { toast.error(err?.response?.data?.detail || "Could not create sub-admin"); }
    finally { setBusy(""); }
  };
  const patch = async (s, body, ok) => {
    setBusy(s.id);
    try { await staffApi.patch(`/admin/subadmins/${s.id}`, body); toast.success(ok); load(); }
    catch (err) { toast.error(err?.response?.data?.detail || "Update failed"); }
    finally { setBusy(""); }
  };
  const saveEdit = async (s, body) => { await staffApi.patch(`/admin/subadmins/${s.id}`, body); toast.success(`${body.name || s.name} updated`); load(); };
  const remove = async (s) => {
    const r = await staffApi.delete(`/admin/subadmins/${s.id}`);
    toast.success(`${s.name} deleted${r.data.released_requests ? ` · ${r.data.released_requests} request(s) released for re-allocation` : ""}`);
    load();
  };

  const inp = "glass rounded-xl px-3 py-2.5 text-sm outline-none";
  return (
    <div className="glass-strong rounded-3xl p-6 mt-6" data-testid="subadmins-manager">
      <div className="flex items-center gap-2 text-sm font-semibold"><UserPlus size={16} className="text-cyan-300" /> Sub-admins · CAs & Associates</div>
      <p className="text-xs text-slate-400 mt-1">Create staff accounts here and tag each as <b>CA</b> or <b>Associate</b> — the Allocate dialog groups them by category.</p>
      <form onSubmit={create} className="mt-4 grid sm:grid-cols-5 gap-3">
        <input data-testid="subadmin-name" required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inp} />
        <input data-testid="subadmin-email" required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inp} />
        <input data-testid="subadmin-password" required type="text" placeholder="Password (min 6)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className={inp} />
        <div className="flex rounded-xl overflow-hidden border border-white/10" data-testid="subadmin-category">
          {CATS.map((c) => (
            <button key={c} type="button" data-testid={`subadmin-category-${c}`} onClick={() => setForm({ ...form, category: c })}
              className={`flex-1 text-xs font-semibold py-2.5 inline-flex items-center justify-center gap-1 ${form.category === c ? "bg-cyan-500 text-slate-950" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
              {c === "CA" ? <IdentificationBadge size={14} /> : <Briefcase size={14} />}{c}
            </button>
          ))}
        </div>
        <button data-testid="subadmin-create" disabled={busy === "create"} className="btn-primary justify-center disabled:opacity-50 !py-2.5 text-sm">
          {busy === "create" ? "Creating…" : `Create ${form.category}`}
        </button>
      </form>

      <div className="mt-5 grid md:grid-cols-2 gap-2">
        {subs.map((s) => (
          <div key={s.id} data-testid={`subadmin-row-${s.id}`} className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium">{s.name}</span>
                <span data-testid={`subadmin-cat-${s.id}`} className={`text-[10px] uppercase px-2 py-0.5 rounded-full border ${catStyle(s.category)}`}>{s.category || "Uncategorised"}</span>
                <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full ${s.active ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-500/20 text-slate-400"}`}>{s.active ? "Active" : "Inactive"}</span>
              </div>
              <div className="text-xs text-slate-400 truncate">{s.email} · {s.service_requests_open ?? 0} open request{s.service_requests_open === 1 ? "" : "s"}</div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <select data-testid={`subadmin-setcat-${s.id}`} value={s.category || ""} disabled={busy === s.id} onChange={(e) => patch(s, { category: e.target.value }, `${s.name} is now ${e.target.value}`)}
                className="glass rounded-lg px-2 py-1 text-xs bg-transparent">
                <option value="" disabled className="bg-[#0a0f24]">Set category</option>
                {CATS.map((c) => <option key={c} value={c} className="bg-[#0a0f24]">{c}</option>)}
              </select>
              <button data-testid={`subadmin-edit-${s.id}`} title="Edit name, email, password, category" onClick={() => setEditing(s)}
                className="rounded-lg p-1.5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/5"><PencilSimple size={14} /></button>
              <button data-testid={`subadmin-toggle-${s.id}`} onClick={() => patch(s, { active: !s.active }, s.active ? "Deactivated" : "Activated")} disabled={busy === s.id}
                className="text-slate-300 hover:text-white flex items-center gap-1 text-xs">
                {s.active ? <ToggleRight size={22} weight="fill" className="text-emerald-400" /> : <ToggleLeft size={22} className="text-slate-500" />}
              </button>
            </div>
          </div>
        ))}
        {subs.length === 0 && <div className="text-sm text-slate-400">No sub-admins yet.</div>}
      </div>
      {editing && <SubAdminEditModal sub={editing} onClose={() => setEditing(null)} onSave={(body) => saveEdit(editing, body)} onDelete={() => remove(editing)} />}
    </div>
  );
}
