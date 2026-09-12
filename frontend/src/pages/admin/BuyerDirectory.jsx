import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { staffApi } from "@/lib/staffAuth";
import { Modal, Banner, input } from "./user/Modal";
import { errText } from "@/lib/adminOps";
import { PencilSimple, Trash, UserPlus, MagnifyingGlass } from "@phosphor-icons/react";

export default function BuyerDirectory({ onEdit, onTotal, refreshKey }) {
  const [rows, setRows] = useState([]), [q, setQ] = useState(""), [page, setPage] = useState(1);
  const [total, setTotal] = useState(0), [err, setErr] = useState(""), [loading, setLoading] = useState(true);
  const [record, setRecord] = useState(null), [mode, setMode] = useState("review"), [phrase, setPhrase] = useState("");
  const [busy, setBusy] = useState(false), [feedback, setFeedback] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let live = true; setLoading(true);
    const timer = setTimeout(() => adminApi.get("/buyers/admin/list", { params: {q, page, limit: 25} }).then(r => {
      if (live) { setRows(r.data.buyers); setTotal(r.data.total); onTotal?.(r.data.total); setErr(""); }
    }).catch(e => live && setErr(errText(e))).finally(() => live && setLoading(false)), 250);
    return () => { live = false; clearTimeout(timer); };
  }, [q, page, version, refreshKey, onTotal]);
  const inspect = async (b, action) => {
    setErr(""); setFeedback(""); setPhrase(""); setMode(action);
    try { setRecord((await staffApi.get(`/admin/buyer-records/${b.geid}`)).data); }
    catch (e) { setErr(errText(e)); }
  };
  const approve = async (id) => {
    setBusy(true); setFeedback("");
    try {
      const { data } = await staffApi.post(`/admin/buyer-records/${record.buyer.geid}/add-user`, {request_id:id}, {timeout:180000});
      const r = data.results[0];
      if (r.status !== "approved") throw new Error(r.error || r.status);
      setFeedback("User approved and linked to this buyer."); setVersion(v => v + 1);
      setRecord((await staffApi.get(`/admin/buyer-records/${record.buyer.geid}`)).data);
    } catch (e) { setFeedback(errText(e)); }
    finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try {
      await staffApi.post(`/admin/buyer-records/${record.buyer.geid}/hard-delete`, {confirm:phrase, linked_uids:record.linked_uids}, {timeout:180000});
      setRecord(null); setVersion(v => v + 1);
    } catch (e) { setFeedback(errText(e)); }
    finally { setBusy(false); }
  };
  return <section data-testid="buyer-directory" className="space-y-4 min-w-0">
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-2 border border-white/10 rounded-lg px-3 flex-1 min-w-0"><MagnifyingGlass size={18} /><input aria-label="Search buyers" data-testid="admin-buyers-search" value={q} onChange={e => {setQ(e.target.value); setPage(1);}} placeholder="Company, email, mobile, GEID…" className="bg-transparent py-3 outline-none min-w-0 w-full" /></div>
      <span data-testid="buyer-directory-count" className="text-sm text-slate-400">{total.toLocaleString()} buyers</span>
    </div>
    <Banner testid="buyer-directory-error">{err}</Banner>
    <div className="flex flex-wrap gap-4 text-xs" data-testid="buyer-directory-legend"><span className="text-amber-300">● Registry match / KYC pending</span><span className="text-emerald-300">● Approved member</span><span className="text-slate-400">● Registry buyer</span></div>
    <table className="w-full text-sm admin-responsive-table table-fixed" data-testid="buyer-directory-table">
      <thead className="text-left text-xs text-slate-400 border-b border-white/10"><tr>{["Name / company", "Mobile", "Email", "Address", "Country", "Actions"].map(t => <th className="p-2" key={t}>{t}</th>)}</tr></thead>
      <tbody>{rows.map(b => <tr data-testid={`admin-buyer-row-${b.geid}`} key={b.geid} className={`border-b border-white/10 align-top ${b.registry_matches?.length ? "bg-amber-500/[.08]" : b.member_verified ? "bg-emerald-500/[.07]" : ""}`}>
        <td className="p-2 break-words" data-testid={`buyer-name-${b.geid}`}>{b.display_name || b.legal_name}<div className="text-xs text-slate-400 mt-1">{b.members?.map(m => m.name).filter(Boolean).join(", ")}</div>{b.registry_matches?.length > 0 && <span data-testid={`buyer-pending-${b.geid}`} className="text-xs text-amber-300">KYC pending</span>}</td>
        <td className="p-2 break-words" data-testid={`buyer-mobile-${b.geid}`}>{b.contact?.phone || b.members?.find(m => m.mobile)?.mobile || "—"}</td>
        <td className="p-2 break-all" data-testid={`buyer-email-${b.geid}`}>{b.contact?.email || b.members?.find(m => m.email)?.email || "—"}</td>
        <td className="p-2 break-words" data-testid={`buyer-address-${b.geid}`}>{b.contact?.address || b.city || "—"}</td>
        <td className="p-2 break-words" data-testid={`buyer-country-${b.geid}`}>{b.country_name || b.country || "—"}</td>
        <td className="p-2"><div className="flex flex-wrap gap-2">
          <button data-testid={`admin-buyer-add-user-${b.geid}`} title="Add user / review KYC" onClick={() => inspect(b, "review")} className="btn-ghost !p-2 text-xs"><UserPlus size={16} /> Add User</button>
          <button data-testid={`admin-buyer-edit-${b.geid}`} title="Edit buyer" onClick={() => onEdit(b)} className="btn-ghost !p-2"><PencilSimple size={16} /></button>
          <button data-testid={`admin-buyer-delete-${b.geid}`} title="Hard delete buyer and linked accounts" onClick={() => inspect(b, "delete")} className="btn-ghost !p-2 text-rose-300"><Trash size={16} /> <span className="text-xs">Hard Delete</span></button>
        </div></td>
      </tr>)}</tbody>
    </table>
    {loading && <p data-testid="buyer-directory-loading" className="text-sm text-slate-400">Loading buyers…</p>}
    {!loading && !rows.length && <p data-testid="buyer-directory-empty">No buyers found.</p>}
    <div className="flex justify-between items-center gap-2 text-xs"><span data-testid="buyer-directory-page">Page {page} of {Math.max(1, Math.ceil(total/25))}</span><div className="flex gap-2"><button data-testid="buyer-directory-prev" disabled={page <= 1} onClick={() => setPage(p => p-1)} className="btn-ghost !py-2 disabled:opacity-40">Previous</button><button data-testid="buyer-directory-next" disabled={page*25 >= total} onClick={() => setPage(p => p+1)} className="btn-ghost !py-2 disabled:opacity-40">Next</button></div></div>
    {record && <Modal wide testid="buyer-record-modal" title={record.buyer.legal_name} kicker={mode === "delete" ? "Permanent removal" : "Registry onboarding review"} onClose={() => !busy && setRecord(null)}>
      <Banner kind="info" testid="buyer-record-feedback">{feedback}</Banner>
      {!record.users.length && <p data-testid="buyer-no-applicants" className="text-sm text-slate-400">No registered user has claimed this company yet.</p>}
      {record.users.map(u => <div key={u.uid} data-testid={`buyer-applicant-${u.uid}`} className="border-b border-white/10 pb-4 mb-4 break-words">
        <p>{u.name || u.email}</p><p className="text-xs text-slate-400 break-all">{u.email} · {u.uid}</p>
        {mode === "review" && <><p className="text-sm mt-2" data-testid={`buyer-kyc-status-${u.uid}`}>KYC: {u.submission.status || "Not submitted"}</p><div className="flex flex-wrap gap-3 mt-2">{["selfie_file_id", "document_file_id"].map(k => u.submission[k] && <a key={k} data-testid={`buyer-kyc-${u.uid}-${k}`} className="text-sm text-cyan-300 underline" target="_blank" rel="noreferrer" href={`${process.env.REACT_APP_BACKEND_URL}/api/storage/file/${u.submission[k]}`}>{k === "selfie_file_id" ? "View selfie" : "View company KYC"}</a>)}</div>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap break-all mt-2" data-testid={`buyer-checks-${u.uid}`}>{JSON.stringify(u.submission.checks || {}, null, 2)}</pre>
          {u.requests.map(r => <button key={r.id} data-testid={`buyer-approve-applicant-${r.id}`} onClick={() => approve(r.id)} disabled={busy || !u.submission.selfie_file_id || !u.submission.document_file_id} className="btn-primary !py-2 mt-3 disabled:opacity-40">Approve KYC & Add User</button>)}
        </>}
      </div>)}
      {mode === "delete" && <><p className="text-sm text-rose-300" data-testid="buyer-delete-warning">This removes the buyer and all {record.linked_uids.length} linked account(s) shown above, including their sign-in access. This cannot be undone.</p><input aria-label="Type DELETE" data-testid="buyer-delete-confirm" className={`${input} mt-3`} placeholder="Type DELETE" value={phrase} onChange={e => setPhrase(e.target.value)} /><button data-testid="buyer-delete-submit" onClick={remove} disabled={busy || phrase !== "DELETE"} className="btn-primary mt-3 disabled:opacity-40">{busy ? "Deleting…" : "Confirm Hard Delete"}</button></>}
    </Modal>}
  </section>;
}