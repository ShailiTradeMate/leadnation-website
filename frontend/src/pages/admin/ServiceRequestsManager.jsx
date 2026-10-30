import React, { useEffect, useMemo, useState } from "react";
import { adminApi } from "@/lib/admin";
import { toast } from "sonner";
import { ResponsiveSelect } from "@/components/ui/responsive-select";
import EmailCaModal from "@/pages/admin/EmailCaModal";
import ServiceRequestDrawer from "@/pages/admin/ServiceRequestDrawer";

export const CLOSED = ["completed", "cancelled"];
const EXTERNAL = "__external__";

function Filters({ f, setF, meta, services }) {
  const inp = "glass rounded-lg px-3 py-2 text-xs";
  return (
    <div className="flex flex-wrap gap-2 items-center mb-3" data-testid="sr-filters">
      <input data-testid="sr-filter-search" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} placeholder="Search name / email / phone" className={`${inp} w-56`} />
      <ResponsiveSelect data-testid="sr-filter-status" value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All statuses</option>
        {meta.statuses.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
      </ResponsiveSelect>
      <ResponsiveSelect data-testid="sr-filter-ca" value={f.ca} onChange={(e) => setF({ ...f, ca: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All CAs</option>
        <option value="__none__" className="bg-[#0a0f24]">Unassigned</option>
        {meta.cas.map((c) => <option key={c.id} value={c.name} className="bg-[#0a0f24]">{c.name}</option>)}
      </ResponsiveSelect>
      <ResponsiveSelect data-testid="sr-filter-service" value={f.service} onChange={(e) => setF({ ...f, service: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All services</option>
        {services.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
      </ResponsiveSelect>
      <button data-testid="sr-filter-unassigned" onClick={() => setF({ ...f, ca: f.ca === "__none__" ? "" : "__none__", status: "" })}
        className={`rounded-lg px-3 py-2 text-xs font-semibold border ${f.ca === "__none__" ? "bg-amber-400/20 border-amber-400/50 text-amber-200" : "border-white/10 text-slate-300 hover:bg-white/5"}`}>
        Unassigned only
      </button>
      {(f.q || f.status || f.ca || f.service) && <button data-testid="sr-filter-clear" onClick={() => setF({ q: "", status: "", ca: "", service: "" })} className="text-xs text-slate-400 underline">Clear</button>}
    </div>
  );
}

function CaCell({ it, meta, onSave, disabled }) {
  const known = meta.cas.find((c) => c.id === it.assignedCaId);
  const mode = it.assignedCaId ? it.assignedCaId : (it.assignedCa ? EXTERNAL : "");
  const [email, setEmail] = useState(it.assignedCaEmail || "");
  const [extName, setExtName] = useState(it.assignedCaId ? "" : (it.assignedCa || ""));
  useEffect(() => { setEmail(it.assignedCaEmail || ""); setExtName(it.assignedCaId ? "" : (it.assignedCa || "")); }, [it.assignedCaEmail, it.assignedCa, it.assignedCaId]);
  const inp = "glass rounded-lg px-2 py-1 text-xs disabled:opacity-40";
  const pick = (v) => {
    if (!v) return onSave({ clearCa: true });
    if (v === EXTERNAL) return onSave({ assignedCaId: null, assignedCa: extName || "External CA", assignedCaEmail: email || null });
    const ca = meta.cas.find((c) => c.id === v);
    onSave({ assignedCaId: v, assignedCa: ca?.name, assignedCaEmail: ca?.email || "" });
  };
  return (
    <div className="flex flex-col gap-1 min-w-[170px]">
      <ResponsiveSelect data-testid={`admin-sr-ca-${it.id}`} value={mode} disabled={disabled} onChange={(e) => pick(e.target.value)} className={inp}>
        <option value="" className="bg-[#0a0f24]">— Unassigned —</option>
        {meta.cas.map((c) => <option key={c.id} value={c.id} className="bg-[#0a0f24]">{c.name}</option>)}
        <option value={EXTERNAL} className="bg-[#0a0f24]">External CA…</option>
      </ResponsiveSelect>
      {mode === EXTERNAL && (
        <input data-testid={`admin-sr-ca-name-${it.id}`} value={extName} disabled={disabled} onChange={(e) => setExtName(e.target.value)}
          onBlur={() => extName.trim() && extName !== it.assignedCa && onSave({ assignedCa: extName.trim() })} placeholder="CA name" className={inp} />
      )}
      <input data-testid={`admin-sr-ca-email-${it.id}`} type="email" value={email} disabled={disabled} onChange={(e) => setEmail(e.target.value)}
        onBlur={() => email.trim().toLowerCase() !== (it.assignedCaEmail || "") && onSave({ assignedCaEmail: email.trim() })}
        placeholder={known?.email || "CA email"} className={inp} />
    </div>
  );
}

export default function ServiceRequestsManager() {
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({ statuses: ["new", "assigned", "in-progress", "completed", "cancelled"], cas: [] });
  const [f, setF] = useState({ q: "", status: "", ca: "", service: "" });
  const [emailing, setEmailing] = useState(null);
  const [openId, setOpenId] = useState(null);
  const reload = () => adminApi.get("/admin/service-requests").then((r) => setItems(r.data)).catch(() => toast.error("Could not load service requests"));
  useEffect(() => { reload(); adminApi.get("/admin/service-requests/ca-options").then((r) => setMeta(r.data)).catch(() => {}); }, []);

  const save = async (id, patch) => {
    try {
      const r = await adminApi.put(`/admin/service-requests/${id}`, patch);
      setItems((xs) => xs.map((x) => (x.id === id ? r.data : x)));
      toast.success("Saved");
      return r.data;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed");
      reload();
    }
  };

  const services = useMemo(() => [...new Set(items.map((i) => i.service).filter(Boolean))].sort(), [items]);
  const shown = useMemo(() => items.filter((it) => {
    const q = f.q.trim().toLowerCase();
    if (q && !`${it.name} ${it.email} ${it.phone} ${it.accountEmail || ""}`.toLowerCase().includes(q)) return false;
    if (f.status && (it.status || "new") !== f.status) return false;
    if (f.ca === "__none__" && it.assignedCa) return false;
    if (f.ca && f.ca !== "__none__" && it.assignedCa !== f.ca) return false;
    if (f.service && it.service !== f.service) return false;
    return true;
  }), [items, f]);

  return (
    <div>
      <Filters f={f} setF={setF} meta={meta} services={services} />
      <div className="text-xs text-slate-500 mb-2" data-testid="sr-count">{shown.length} of {items.length} requests</div>
      <div className="glass-strong rounded-3xl overflow-x-auto">
        <table className="w-full text-sm min-w-[1100px]">
          <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
            <tr>
              <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Service</th>
              <th className="text-left px-4 py-3">Name</th><th className="text-left px-4 py-3">Email / Phone</th>
              <th className="text-left px-4 py-3">Status</th><th className="text-left px-4 py-3">Assigned CA · email</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((it) => {
              const closed = CLOSED.includes(it.status);
              return (
                <tr key={it.id} data-testid={`admin-sr-row-${it.id}`} onClick={() => setOpenId(it.id)} title="Open request" className={`border-t border-white/5 align-top cursor-pointer hover:bg-white/[0.03] ${closed ? "opacity-70" : ""}`}>
                  <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">{(it.createdAt || "").slice(0, 16).replace("T", " ")}</td>
                  <td className="px-4 py-3 text-xs text-cyan-300 font-mono-display"><div>{it.service}</div>{it.entity && <div className="text-slate-400 mt-0.5">{it.entity}</div>}</td>
                  <td className="px-4 py-3">{it.name}{it.customerId && <div className="text-[10px] text-slate-500 font-mono-display">ID {it.customerId}</div>}</td>
                  <td className="px-4 py-3 text-xs"><div>{it.email}</div><div className="text-slate-500">{it.phone}</div></td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <ResponsiveSelect data-testid={`admin-sr-status-${it.id}`} value={it.status || "new"} onChange={(e) => save(it.id, { status: e.target.value })} className="glass rounded-lg px-2 py-1 text-xs">
                      {meta.statuses.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
                    </ResponsiveSelect>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}><CaCell it={it} meta={meta} disabled={closed} onSave={(p) => save(it.id, p)} /></td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <button data-testid={`admin-sr-email-ca-${it.id}`} disabled={closed} onClick={() => setEmailing(it)} title={closed ? "Completed/cancelled requests cannot be allocated" : "Email the CA"}
                      className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-cyan-500/30">
                      Email CA
                    </button>
                    {it.caNotifiedAt && <div className="text-[10px] text-emerald-300 mt-1">CA notified ✓ {it.caNotifiedAt.slice(0, 10)}</div>}
                  </td>
                </tr>
              );
            })}
            {shown.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">{items.length ? "No requests match these filters." : "No service requests yet."}</td></tr>}
          </tbody>
        </table>
      </div>
      {emailing && <EmailCaModal item={emailing} onClose={() => setEmailing(null)} onSent={(upd) => setItems((xs) => xs.map((x) => (x.id === upd.id ? upd : x)))} />}
      {openId && items.find((x) => x.id === openId) && (
        <ServiceRequestDrawer item={items.find((x) => x.id === openId)} meta={meta} onClose={() => setOpenId(null)}
          onSave={(p) => save(openId, p)} onEmailCa={(it) => setEmailing(it)} />
      )}
    </div>
  );
}
