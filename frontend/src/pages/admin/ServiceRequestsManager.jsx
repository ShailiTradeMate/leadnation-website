import React, { useEffect, useMemo, useState } from "react";
import { adminApi } from "@/lib/admin";
import { toast } from "sonner";
import { ResponsiveSelect } from "@/components/ui/responsive-select";
import EmailCaModal from "@/pages/admin/EmailCaModal";
import ServiceRequestDrawer from "@/pages/admin/ServiceRequestDrawer";
import AllocateModal from "@/pages/admin/AllocateModal";
import { staffApi } from "@/lib/staffAuth";

export const CLOSED = ["completed", "cancelled"];
const EXTERNAL = "__external__";

function Filters({ f, setF, meta, services, showCa = true }) {
  const inp = "glass rounded-lg px-3 py-2 text-xs";
  return (
    <div className="flex flex-wrap gap-2 items-center mb-3" data-testid="sr-filters">
      <input data-testid="sr-filter-search" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} placeholder="Search name / email / phone" className={`${inp} w-56`} />
      <ResponsiveSelect data-testid="sr-filter-status" value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All statuses</option>
        {meta.statuses.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
      </ResponsiveSelect>
      {showCa && <ResponsiveSelect data-testid="sr-filter-ca" value={f.ca} onChange={(e) => setF({ ...f, ca: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All CAs</option>
        <option value="__none__" className="bg-[#0a0f24]">Unassigned</option>
        {meta.cas.map((c) => <option key={c.id} value={c.name} className="bg-[#0a0f24]">{c.name}</option>)}
      </ResponsiveSelect>}
      <ResponsiveSelect data-testid="sr-filter-service" value={f.service} onChange={(e) => setF({ ...f, service: e.target.value })} className={inp}>
        <option value="" className="bg-[#0a0f24]">All services</option>
        {services.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
      </ResponsiveSelect>
      {showCa && <button data-testid="sr-filter-unassigned" onClick={() => setF({ ...f, ca: f.ca === "__none__" ? "" : "__none__", status: "" })}
        className={`rounded-lg px-3 py-2 text-xs font-semibold border ${f.ca === "__none__" ? "bg-amber-400/20 border-amber-400/50 text-amber-200" : "border-white/10 text-slate-300 hover:bg-white/5"}`}>
        Unassigned only
      </button>}
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
        {meta.cas.map((c) => <option key={c.id} value={c.id} className="bg-[#0a0f24]">{c.name}{c.category && c.category !== "Uncategorised" ? ` (${c.category})` : ""}</option>)}
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

export default function ServiceRequestsManager({ mode = "admin", onSummary }) {
  const staff = mode === "staff";
  const http = staff ? staffApi : adminApi;
  const base = staff ? "/staff/service-requests" : "/admin/service-requests";
  const [items, setItems] = useState([]);
  const [me, setMe] = useState(null);
  const [meta, setMeta] = useState({ statuses: ["new", "assigned", "in-progress", "Partial payment received", "Full payment received", "completed", "cancelled"], cas: [] });
  const [f, setF] = useState({ q: "", status: "", ca: "", service: "" });
  const [emailing, setEmailing] = useState(null);
  const [allocating, setAllocating] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [seenIds, setSeenIds] = useState(() => new Set());
  const unread = (it) => Boolean(it.hasUnreadReply) && !seenIds.has(it.id);

  const reload = () => http.get(base).then((r) => {
    if (staff) { setItems(r.data.items); setMe(r.data.me); setMeta((m) => ({ ...m, statuses: r.data.statuses })); }
    else setItems(r.data);
  }).catch(() => toast.error("Could not load service requests"));
  useEffect(() => {
    reload();
    if (!staff) adminApi.get("/admin/service-requests/ca-options").then((r) => setMeta(r.data)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);
  useEffect(() => {
    if (!onSummary) return;
    const open = items.filter((i) => !CLOSED.includes(i.status));
    onSummary((prev) => ({ ...(prev || {}), open: open.length, new: open.filter((i) => i.isNew).length, unassigned: open.filter((i) => !i.assignedCa).length, unreadReplies: items.filter(unread).length }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, onSummary, seenIds]);

  const replace = (upd) => setItems((xs) => xs.map((x) => (x.id === upd.id ? { ...upd, isNew: false } : x)));
  const save = async (id, patch) => {
    try {
      const r = await http.put(`${base}/${id}`, patch);
      replace(r.data);
      toast.success("Saved");
      return r.data;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed");
      reload();
    }
  };
  const openRow = (it) => {
    setOpenId(it.id);
    setSeenIds((s) => new Set(s).add(it.id));
    if (staff) { http.post(`${base}/${it.id}/open`).catch(() => {}); }
    else if (it.hasUnreadReply) { adminApi.post(`/admin/service-requests/${it.id}/seen`).catch(() => {}); }
    if (it.isNew) replace({ ...it });
  };
  const checkReplies = async () => {
    try {
      const r = await staffApi.post("/staff/service-requests/inbox/poll");
      if (r.data.ok === false) { toast.error(r.data.reason || "Mailbox not configured"); return; }
      toast.success(r.data.matched ? `${r.data.matched} new repl${r.data.matched === 1 ? "y" : "ies"} added` : "No new replies");
      if (r.data.matched) await reload();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not check the mailbox"); }
  };
  const sendMessage = async (id, body) => {
    let r;
    if (body.files?.length) {
      const fd = new FormData();
      fd.append("message", body.message || "");
      fd.append("extraCc", (body.extraCc || []).join(","));
      body.files.forEach((f) => fd.append("files", f));
      r = await staffApi.post(`/staff/service-requests/${id}/email-customer-files`, fd, { headers: { "Content-Type": "multipart/form-data" } });
    } else {
      r = await http.post(`${base}/${id}/email-customer`, { message: body.message, extraCc: body.extraCc });
    }
    replace(r.data.item);
    toast.success(`Emailed ${r.data.to}${r.data.cc.length ? ` · CC ${r.data.cc.join(", ")}` : ""}`);
  };
  const downloadFile = async (id, f) => {
    try {
      const r = await staffApi.get(`/staff/service-requests/${id}/files/${f.id}`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a"); a.href = url; a.download = f.filename; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch { toast.error("Could not download the file"); }
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
  const current = openId ? items.find((x) => x.id === openId) : null;

  return (
    <div>
      {staff && me && !me.isMain && (
        <div className="mb-3 text-xs text-slate-400" data-testid="staff-sr-intro">
          Showing requests allocated to <span className="text-slate-100 font-semibold">{me.name || me.email}</span>. Open a row to update status, add notes or email the customer.
        </div>
      )}
      <Filters f={f} setF={setF} meta={meta} services={services} showCa={!staff} />
      <div className="text-xs text-slate-500 mb-2" data-testid="sr-count">{shown.length} of {items.length} requests</div>
      <div className="glass-strong rounded-3xl overflow-x-auto">
        <table className={`w-full text-sm ${staff ? "min-w-[900px]" : "min-w-[1180px]"}`}>
          <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
            <tr>
              <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Service</th>
              <th className="text-left px-4 py-3">Name</th><th className="text-left px-4 py-3">Email / Phone</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">{staff ? "Assigned" : "Assigned CA · email"}</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((it) => {
              const closed = CLOSED.includes(it.status);
              return (
                <tr key={it.id} data-testid={`admin-sr-row-${it.id}`} onClick={() => openRow(it)} title="Open request" className={`border-t border-white/5 align-top cursor-pointer hover:bg-white/[0.03] ${closed ? "opacity-70" : ""}`}>
                  <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                    {(it.createdAt || "").slice(0, 16).replace("T", " ")}
                    {it.isNew && <span data-testid={`sr-new-badge-${it.id}`} className="ml-2 rounded-full px-2 py-0.5 text-[10px] font-bold bg-amber-400/20 text-amber-200 border border-amber-400/40">NEW</span>}
                    {unread(it) && (
                      <span data-testid={`sr-reply-badge-${it.id}`} className="ml-2 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-200 border border-emerald-400/50">
                        <span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" /><span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" /></span>
                        {it.lastReplyRole === "customer" ? "Customer replied" : `${it.lastReplyRole || "New"} reply`}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-cyan-300 font-mono-display"><div>{it.service}</div>{it.entity && <div className="text-slate-400 mt-0.5">{it.entity}</div>}</td>
                  <td className="px-4 py-3">{it.name}{it.customerId && <div className="text-[10px] text-slate-500 font-mono-display">ID {it.customerId}</div>}</td>
                  <td className="px-4 py-3 text-xs"><div>{it.email}</div><div className="text-slate-500">{it.phone}</div></td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <ResponsiveSelect data-testid={`admin-sr-status-${it.id}`} value={it.status || "new"} disabled={staff && !me?.isMain && it.status === "completed"} onChange={(e) => save(it.id, { status: e.target.value })} className="glass rounded-lg px-2 py-1 text-xs disabled:opacity-50">
                      {meta.statuses.map((s) => <option key={s} value={s} className="bg-[#0a0f24]">{s}</option>)}
                    </ResponsiveSelect>
                  </td>
                  {staff ? (
                    <td className="px-4 py-3 text-xs"><div className="text-emerald-300 font-semibold">{me?.isMain ? (it.assignedCa || "— Unassigned —") : "You"}</div>{it.assignedCaEmail && <div className="text-slate-500">{it.assignedCaEmail}</div>}</td>
                  ) : (
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}><CaCell it={it} meta={meta} disabled={closed} onSave={(p) => save(it.id, p)} /></td>
                  )}
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    {staff ? (
                      <button data-testid={`staff-sr-open-${it.id}`} onClick={() => openRow(it)} className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-500/30">Open · Email customer</button>
                    ) : (
                      <div className="flex flex-col gap-1.5">
                        <button data-testid={`admin-sr-allocate-${it.id}`} disabled={closed} onClick={() => setAllocating(it)} title={closed ? "Completed/cancelled requests cannot be allocated" : "Allocate to a CA / employee"}
                          className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed">
                          {it.assignedCa ? "Re-allocate" : "Allocate"}
                        </button>
                        <button data-testid={`admin-sr-email-ca-${it.id}`} disabled={closed} onClick={() => setEmailing(it)} title={closed ? "Completed/cancelled requests cannot be allocated" : "Email the CA"}
                          className="rounded-lg px-3 py-1.5 text-xs font-semibold bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-cyan-500/30">
                          Email CA
                        </button>
                      </div>
                    )}
                    {it.caNotifiedAt && <div className="text-[10px] text-emerald-300 mt-1">CA notified ✓ {it.caNotifiedAt.slice(0, 10)}</div>}
                  </td>
                </tr>
              );
            })}
            {shown.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">{items.length ? "No requests match these filters." : (staff ? "No requests allocated to you yet." : "No service requests yet.")}</td></tr>}
          </tbody>
        </table>
      </div>
      {emailing && <EmailCaModal item={emailing} onClose={() => setEmailing(null)} onSent={replace} />}
      {allocating && <AllocateModal item={allocating} meta={meta} onClose={() => setAllocating(null)} onDone={replace} />}
      {current && (
        <ServiceRequestDrawer item={current} meta={meta} onClose={() => setOpenId(null)}
          onSave={(p) => save(openId, p)} onEmailCa={(it) => setEmailing(it)} onAllocate={staff ? null : (it) => setAllocating(it)}
          caReadOnly={staff} canEmailCa={!staff} statusLocked={staff && !me?.isMain && current.status === "completed"}
          onSendMessage={(body) => sendMessage(openId, body)} onCheckReplies={checkReplies} onDownloadFile={(f) => downloadFile(openId, f)} />
      )}
    </div>
  );
}
