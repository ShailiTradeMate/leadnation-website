import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { toast } from "sonner";
import {
  ShieldCheck, MagnifyingGlass, Trash, PencilSimple, DownloadSimple,
  ArrowsClockwise, BellRinging, CheckCircle, XCircle, FloppyDisk,
} from "@phosphor-icons/react";

export default function BuyersManager() {
  const [qa, setQa] = useState(null);
  const [status, setStatus] = useState(null);
  const [notifs, setNotifs] = useState({ notifications: [], unread: 0 });
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);

  const loadList = async () => {
    const { data } = await adminApi.get(`/buyers/admin/list`, { params: { q, page, limit: 25 } });
    setRows(data.buyers); setTotal(data.total);
  };
  const loadMeta = async () => {
    adminApi.get(`/buyers/admin/qa`).then((r) => setQa(r.data)).catch(() => {});
    adminApi.get(`/buyers/ingest/status`).then((r) => setStatus(r.data)).catch(() => {});
    adminApi.get(`/buyers/admin/notifications`).then((r) => setNotifs(r.data)).catch(() => {});
  };
  useEffect(() => { loadMeta(); }, []);
  useEffect(() => { loadList(); }, [page]);

  const runIngest = async () => {
    setBusy(true);
    try { await adminApi.post(`/buyers/ingest/run?background=true`); toast.success("Ingestion started — buyers will update shortly."); }
    finally { setBusy(false); }
  };
  const markNotifsRead = async () => {
    await adminApi.post(`/buyers/admin/notifications/read`);
    setNotifs((n) => ({ ...n, unread: 0 }));
  };
  const download = async (kind) => {
    try {
      const res = await adminApi.get(`/buyers/admin/export.${kind}`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url; a.download = `leadnation-buyers.${kind}`; a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${kind.toUpperCase()}`);
    } catch (_) { toast.error("Export failed"); }
  };
  const saveEdit = async () => {
    await adminApi.patch(`/buyers/admin/${editing.geid}`, {
      legal_name: editing.legal_name, country_name: editing.country_name,
      sector: editing.sector, city: editing.city, status: editing.status,
    });
    toast.success("Buyer updated (admin edits persist across daily ingestion)");
    setEditing(null); loadList();
  };
  const del = async (geid) => {
    if (!window.confirm("Delete this buyer? It will not return on daily ingestion.")) return;
    await adminApi.delete(`/buyers/admin/${geid}`);
    toast.success("Buyer deleted"); loadList();
  };
  const bulkDeleteSource = async (source_id) => {
    if (!window.confirm(`Delete ALL buyers from source "${source_id}"?`)) return;
    const { data } = await adminApi.post(`/buyers/admin/delete-bulk`, { scope: "source", source_id });
    toast.success(`Deleted ${data.deleted} buyers`); loadMeta(); loadList();
  };

  const pages = Math.max(1, Math.ceil(total / 25));

  return (
    <div data-testid="admin-buyers" className="space-y-6">
      {/* Header actions */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="font-display font-bold text-xl flex items-center gap-2">
          <ShieldCheck size={20} weight="fill" className="text-cyan-300" /> Verified Buyers — {total.toLocaleString()} records
        </h2>
        <div className="flex items-center gap-2">
          <button data-testid="admin-buyers-ingest" onClick={runIngest} disabled={busy} className="btn-ghost !py-2 text-xs">
            <ArrowsClockwise size={14} weight="bold" /> {busy ? "Running…" : "Run ingestion"}
          </button>
          <button data-testid="admin-buyers-export-xlsx" onClick={() => download("xlsx")} className="btn-ghost !py-2 text-xs">
            <DownloadSimple size={14} weight="bold" /> Excel
          </button>
          <button data-testid="admin-buyers-export-pdf" onClick={() => download("pdf")} className="btn-ghost !py-2 text-xs">
            <DownloadSimple size={14} weight="bold" /> PDF
          </button>
        </div>
      </div>

      {/* QA + notifications */}
      <div className="grid md:grid-cols-3 gap-4">
        <div data-testid="admin-buyers-qa" className="glass rounded-2xl p-4 md:col-span-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Data Quality Audit</span>
            {qa && (qa.overall_pass
              ? <span className="text-xs text-emerald-300 flex items-center gap-1"><CheckCircle size={14} weight="fill" /> All checks pass</span>
              : <span className="text-xs text-rose-300 flex items-center gap-1"><XCircle size={14} weight="fill" /> Issues found</span>)}
          </div>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {qa && Object.entries(qa.checks).map(([k, c]) => (
              <div key={k} className="text-[11px] flex items-center gap-1.5">
                {c.pass ? <CheckCircle size={13} weight="fill" className="text-emerald-300" /> : <XCircle size={13} weight="fill" className="text-rose-300" />}
                <span className="text-slate-400">{k.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
          {status && status.runs?.[0] && (
            <div className="mt-3 text-[11px] text-slate-500">
              Last run: +{status.runs[0].new_buyers ?? status.runs[0].upserted} new · screened out {status.runs[0].screened_out} · sources {Object.entries(status.runs[0].sources || {}).map(([s, n]) => `${s}:${n}`).join(", ")}
            </div>
          )}
        </div>
        <div className="glass rounded-2xl p-4">
          <button data-testid="admin-buyers-bell" onClick={markNotifsRead} className="w-full flex items-center justify-between">
            <span className="text-sm font-semibold flex items-center gap-2"><BellRinging size={16} weight="fill" className="text-amber-300" /> Notifications</span>
            {notifs.unread > 0 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200">{notifs.unread} new</span>}
          </button>
          <div className="mt-3 space-y-2 max-h-32 overflow-auto">
            {(notifs.notifications || []).slice(0, 5).map((n, i) => (
              <div key={i} className="text-[11px] text-slate-400 border-b border-white/5 pb-1.5">
                <div className="text-slate-200">{n.title}</div>{(n.body || "").slice(0, 90)}
              </div>
            ))}
            {(!notifs.notifications || !notifs.notifications.length) && <div className="text-[11px] text-slate-500">No notifications yet.</div>}
          </div>
        </div>
      </div>

      {/* Bulk delete by source */}
      {status && (
        <div className="glass rounded-2xl p-3 flex items-center gap-2 flex-wrap text-xs">
          <span className="text-slate-400">Delete by source:</span>
          {Object.keys(status.runs?.[0]?.sources || {}).filter((s) => (status.runs[0].sources[s] > 0)).map((s) => (
            <button key={s} onClick={() => bulkDeleteSource(s)} className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-200 border border-rose-400/20 hover:bg-rose-500/20">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="flex items-center gap-2">
        <div className="flex-1 glass rounded-xl px-3 flex items-center gap-2">
          <MagnifyingGlass size={16} className="text-slate-400" />
          <input data-testid="admin-buyers-search" value={q} onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (setPage(1), loadList())}
            placeholder="Search buyer name, product, city…" className="bg-transparent outline-none text-sm py-2.5 w-full" />
        </div>
        <button onClick={() => { setPage(1); loadList(); }} className="btn-ghost !py-2 text-xs">Search</button>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-white/10">
            <tr>
              <th className="text-left p-3">Buyer</th><th className="text-left p-3">Country</th>
              <th className="text-left p-3">Sector</th><th className="text-left p-3">Trust</th>
              <th className="text-left p-3">Source</th><th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((b) => (
              <tr key={b.geid} data-testid={`admin-buyer-row-${b.geid}`} className="border-b border-white/5 hover:bg-white/5">
                <td className="p-3">{b.display_name}{b.admin_edited && <span className="ml-2 text-[10px] text-amber-300">edited</span>}</td>
                <td className="p-3 text-slate-400">{b.country_name}</td>
                <td className="p-3 text-slate-400">{b.sector}</td>
                <td className="p-3">{b.trust?.score} <span className="text-[10px] text-slate-500">{b.trust?.band}</span></td>
                <td className="p-3 text-[11px] text-slate-500">{(b.created_by || "").replace("vbie-connector:", "")}</td>
                <td className="p-3 text-right whitespace-nowrap">
                  <button data-testid={`admin-buyer-edit-${b.geid}`} onClick={() => setEditing(b)} className="p-1.5 hover:text-cyan-300"><PencilSimple size={15} /></button>
                  <button data-testid={`admin-buyer-delete-${b.geid}`} onClick={() => del(b.geid)} className="p-1.5 hover:text-rose-300"><Trash size={15} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Page {page} of {pages}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-ghost !py-1.5 disabled:opacity-40">Prev</button>
          <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} className="btn-ghost !py-1.5 disabled:opacity-40">Next</button>
        </div>
      </div>

      {/* Edit modal */}
      {editing && (
        <div className="fixed inset-0 z-[90] grid place-items-center bg-black/70 p-4" onClick={() => setEditing(null)}>
          <div data-testid="admin-buyer-edit-modal" className="glass-strong rounded-2xl p-6 w-full max-w-md space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-display font-bold text-lg">Edit buyer</h3>
            {["legal_name", "country_name", "sector", "city"].map((f) => (
              <label key={f} className="block">
                <span className="text-[11px] uppercase tracking-wider text-slate-500">{f.replace("_", " ")}</span>
                <input value={editing[f] || ""} onChange={(e) => setEditing({ ...editing, [f]: e.target.value })}
                  className="w-full glass rounded-xl px-3 py-2 outline-none text-sm mt-1" data-testid={`admin-edit-${f}`} />
              </label>
            ))}
            <label className="block">
              <span className="text-[11px] uppercase tracking-wider text-slate-500">status</span>
              <select value={editing.status || "active"} onChange={(e) => setEditing({ ...editing, status: e.target.value })}
                className="w-full glass rounded-xl px-3 py-2 outline-none text-sm mt-1">
                <option value="active">active</option><option value="deleted">deleted</option>
              </select>
            </label>
            <div className="flex gap-2 pt-2">
              <button data-testid="admin-edit-save" onClick={saveEdit} className="btn-primary flex-1 justify-center"><FloppyDisk size={15} weight="bold" /> Save</button>
              <button onClick={() => setEditing(null)} className="btn-ghost">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
