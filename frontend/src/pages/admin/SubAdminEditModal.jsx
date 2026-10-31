import React, { useState } from "react";
import { X, Trash, FloppyDisk, Warning } from "@phosphor-icons/react";

const CATS = ["CA", "Associate"];

export default function SubAdminEditModal({ sub, onClose, onSave, onDelete }) {
  const [f, setF] = useState({ name: sub.name || "", email: sub.email || "", password: "", category: sub.category || "CA", active: sub.active !== false });
  const [busy, setBusy] = useState("");
  const [confirmDel, setConfirmDel] = useState(false);
  const [err, setErr] = useState("");
  const inp = "glass rounded-xl px-3 py-2.5 text-sm outline-none w-full";
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const save = async (e) => {
    e.preventDefault(); setBusy("save"); setErr("");
    const body = { name: f.name.trim(), email: f.email.trim(), category: f.category, active: f.active };
    if (f.password) body.password = f.password;
    try { await onSave(body); onClose(); } catch (x) { setErr(x?.response?.data?.detail || "Update failed"); } finally { setBusy(""); }
  };
  const del = async () => {
    setBusy("delete"); setErr("");
    try { await onDelete(); onClose(); } catch (x) { setErr(x?.response?.data?.detail || "Delete failed"); setBusy(""); }
  };

  return (
    <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center p-3" onClick={onClose} data-testid="subadmin-edit-modal">
      <form onSubmit={save} onClick={(e) => e.stopPropagation()} className="glass-strong rounded-3xl p-5 sm:p-6 w-full max-w-lg space-y-3">
        <div className="flex items-center justify-between">
          <div className="font-display font-bold">Edit {sub.category || "sub-admin"} · {sub.name}</div>
          <button type="button" data-testid="subadmin-edit-close" onClick={onClose} className="text-slate-400 hover:text-white"><X size={18} /></button>
        </div>
        <label className="block text-xs text-slate-400">Name<input data-testid="subadmin-edit-name" required value={f.name} onChange={set("name")} className={`${inp} mt-1`} /></label>
        <label className="block text-xs text-slate-400">Login email<input data-testid="subadmin-edit-email" required type="email" value={f.email} onChange={set("email")} className={`${inp} mt-1`} /></label>
        <label className="block text-xs text-slate-400">New password <span className="text-slate-500">(leave blank to keep current)</span>
          <input data-testid="subadmin-edit-password" type="text" minLength={6} placeholder="min 6 characters" value={f.password} onChange={set("password")} className={`${inp} mt-1`} autoComplete="new-password" /></label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-slate-400 mb-1">Category</div>
            <div className="flex rounded-xl overflow-hidden border border-white/10">
              {CATS.map((c) => (
                <button key={c} type="button" data-testid={`subadmin-edit-cat-${c}`} onClick={() => setF({ ...f, category: c })}
                  className={`flex-1 text-xs font-semibold py-2.5 ${f.category === c ? "bg-cyan-500 text-slate-950" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>{c}</button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400 mb-1">Status</div>
            <div className="flex rounded-xl overflow-hidden border border-white/10">
              {[["active", true], ["inactive", false]].map(([l, v]) => (
                <button key={l} type="button" data-testid={`subadmin-edit-${l}`} onClick={() => setF({ ...f, active: v })}
                  className={`flex-1 text-xs font-semibold py-2.5 capitalize ${f.active === v ? (v ? "bg-emerald-500 text-slate-950" : "bg-slate-500 text-white") : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>{l}</button>
              ))}
            </div>
          </div>
        </div>
        {err && <div data-testid="subadmin-edit-error" className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2">{err}</div>}
        <div className="flex items-center justify-between gap-2 pt-1 flex-wrap">
          {confirmDel ? (
            <div className="flex items-center gap-2 text-xs text-rose-200 flex-wrap" data-testid="subadmin-delete-confirm">
              <Warning size={14} /> Delete permanently? {sub.service_requests_open ? `${sub.service_requests_open} open request(s) will be released for re-allocation.` : ""}
              <button type="button" data-testid="subadmin-delete-yes" disabled={busy === "delete"} onClick={del} className="rounded-lg px-3 py-1.5 font-semibold bg-rose-500 text-white hover:bg-rose-400 disabled:opacity-50">{busy === "delete" ? "Deleting…" : "Yes, delete"}</button>
              <button type="button" data-testid="subadmin-delete-no" onClick={() => setConfirmDel(false)} className="rounded-lg px-3 py-1.5 border border-white/10 text-slate-300">Cancel</button>
            </div>
          ) : (
            <button type="button" data-testid="subadmin-delete" onClick={() => setConfirmDel(true)} className="inline-flex items-center gap-1 text-xs text-rose-300 hover:text-rose-200"><Trash size={14} /> Delete account</button>
          )}
          <button data-testid="subadmin-edit-save" disabled={busy === "save"} className="btn-primary !py-2 text-sm inline-flex items-center gap-1.5 disabled:opacity-50"><FloppyDisk size={14} /> {busy === "save" ? "Saving…" : "Save changes"}</button>
        </div>
      </form>
    </div>
  );
}
