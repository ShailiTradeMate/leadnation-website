import React, { useEffect, useMemo, useRef, useState } from "react";
import { staffApi } from "@/lib/staffAuth";
import { API } from "@/lib/api";
import AllocatePanel from "@/pages/admin/AllocatePanel";
import ActionBar from "@/pages/admin/user/ActionBar";
import SignoffQueue from "@/pages/admin/user/SignoffQueue";
import DeleteQueue from "@/pages/admin/user/DeleteQueue";
import { adminOps } from "@/lib/adminOps";
import { MagnifyingGlass, CaretDown, CaretUp, FileText, User, Buildings, UsersThree } from "@phosphor-icons/react";

const STATUS_STYLE = {
  verified: "bg-emerald-500/20 text-emerald-300",
  needs_review: "bg-amber-500/20 text-amber-300",
  rejected: "bg-rose-500/20 text-rose-300",
  not_applied: "bg-slate-500/20 text-slate-300",
};
const STATUS_LABEL = {
  verified: "Verified", needs_review: "Needs Review", rejected: "Rejected", not_applied: "Not Applied",
};

function StatusPill({ status }) {
  const s = status || "not_applied";
  return (
    <span data-testid="user-status" className={`text-[10px] font-mono-display uppercase px-2 py-0.5 rounded-full ${STATUS_STYLE[s] || STATUS_STYLE.not_applied}`}>
      {STATUS_LABEL[s] || s.replace(/_/g, " ")}
    </span>
  );
}

function DetailRow({ label, value }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-sm text-slate-200 break-words">{value || "—"}</div>
    </div>
  );
}

const HIDE_KEYS = new Set(["uid", "_id", "customer_id", "name", "full_name", "email", "mobile",
  "mobile_number", "country", "state", "city", "role", "user_role", "company_details",
  "verification_status", "updated_at", "created_at", "geid", "is_deleted"]);

function FullProfile({ uid }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    adminOps.fullProfile(uid).then(setData).catch(() => setErr("Could not load the shared profile."));
  }, [uid]);
  if (err) return <div className="text-xs text-slate-500">{err}</div>;
  if (!data) return <div className="text-xs text-slate-500">Loading full profile…</div>;
  const p = data.profile || {};
  const cd = p.company_details || {};
  const extras = [
    ["City", p.city], ["Address", p.address || p.location],
    ["Products traded", Array.isArray(p.products) ? p.products.join(", ") : p.products],
    ["HSN codes", Array.isArray(p.hsn_codes) ? p.hsn_codes.join(", ") : p.hsn_codes],
    ["GST / Tax ID", cd.gst || cd.tax_id], ["Company address", cd.address],
    ...Object.entries(p).filter(([k, v]) => !HIDE_KEYS.has(k) && v && typeof v !== "object"
      && !["city", "address", "location"].includes(k)).map(([k, v]) => [k.replace(/_/g, " "), String(v)]),
  ].filter(([, v]) => v);
  if (extras.length === 0) return (
    <div className="text-xs text-slate-500" data-testid={`full-profile-empty-${uid}`}>
      No further details on the shared profile — this user has not completed onboarding.
    </div>
  );
  return (
    <div className="grid md:grid-cols-4 gap-4" data-testid={`full-profile-${uid}`}>
      {extras.slice(0, 16).map(([l, v]) => <DetailRow key={l} label={l} value={v} />)}
    </div>
  );
}

function UserDetail({ u, perms, isMain, onRefresh }) {
  return (
    <div className="grid md:grid-cols-3 gap-4 p-5 bg-white/[0.03] border-t border-white/5" data-testid={`user-detail-${u.uid}`}>
      <div className="space-y-3">
        <div className="text-[11px] uppercase tracking-widest text-cyan-300 flex items-center gap-1.5"><User size={13} /> Personal</div>
        <DetailRow label="Full name" value={u.name} />
        <DetailRow label="Email" value={u.email} />
        <DetailRow label="Mobile" value={u.mobile} />
        <DetailRow label="Country" value={u.country} />
        <DetailRow label="State / Province" value={u.state} />
        <DetailRow label="User category" value={u.category || u.user_role} />
        <DetailRow label="User ID (uid)" value={u.uid} />
      </div>
      <div className="space-y-3">
        <div className="text-[11px] uppercase tracking-widest text-cyan-300 flex items-center gap-1.5"><Buildings size={13} /> Company</div>
        <DetailRow label="Company name" value={u.company_name} />
        <DetailRow label="Company email" value={u.company_email} />
        <DetailRow label="Company contact" value={u.company_phone} />
        <DetailRow label="City" value={u.city} />
        <DetailRow label="Products / services" value={Array.isArray(u.products) ? u.products.join(", ") : u.products} />
        <DetailRow label="About the company" value={u.company_description} />
        <DetailRow label="Customer ID" value={u.customer_id} />
        <DetailRow label="Buyer ID (GEID)" value={u.geid} />
        <DetailRow label="Subscription" value={u.subscription?.status ? `${u.subscription.status}${u.subscription.plan ? " · " + u.subscription.plan : ""}` : "None"} />
      </div>
      <div className="space-y-3">
        <div className="text-[11px] uppercase tracking-widest text-cyan-300 flex items-center gap-1.5"><FileText size={13} /> Documents & Status</div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Submitted documents</div>
          {u.documents?.length ? (
            <div className="flex flex-wrap gap-2">
              {u.documents.map((d, i) => (
                <a key={i} href={`${process.env.REACT_APP_BACKEND_URL}${d.url}`} target="_blank" rel="noreferrer"
                  data-testid={`user-doc-${u.uid}-${d.kind}`}
                  className="text-xs px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-cyan-400/40 flex items-center gap-1.5">
                  <FileText size={12} /> {d.label}
                </a>
              ))}
            </div>
          ) : <div className="text-sm text-slate-400">No documents submitted</div>}
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Approval status</div>
          <StatusPill status={u.status} />
        </div>
        {u.reasons?.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Review notes</div>
            <ul className="text-xs text-amber-200 list-disc ml-4 space-y-0.5">{u.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
          </div>
        )}
        {u.assigned_to_name && <DetailRow label="Assigned to" value={u.assigned_to_name} />}
      </div>
      <div className="md:col-span-3 border-t border-white/5 pt-4 grid md:grid-cols-4 gap-4" data-testid={`user-account-${u.uid}`}>
        <DetailRow label="Account state" value={u.account_state} />
        <DetailRow label="Email verified" value={u.email_verified === undefined ? null : (u.email_verified ? "Yes" : "No")} />
        <DetailRow label="Onboarding" value={u.onboarding_status} />
        <DetailRow label="Sign-in method" value={u.provider} />
        <DetailRow label="Identity verification" value={u.identity_verification_status} />
        <DetailRow label="Plan (identity)" value={u.identity_subscription?.status
          ? `${u.identity_subscription.status}${u.identity_subscription.expiry ? " · till " + String(u.identity_subscription.expiry).slice(0, 10) : ""}` : null} />
        <DetailRow label="Registered on" value={u.created_at ? String(u.created_at).slice(0, 16).replace("T", " ") : null} />
        <DetailRow label="Last activity" value={u.last_activity_at ? String(u.last_activity_at).slice(0, 16).replace("T", " ") : null} />
      </div>
      <div className="md:col-span-3 border-t border-white/5 pt-4">
        <div className="text-[11px] uppercase tracking-widest text-cyan-300 mb-3">Shared profile (full record)</div>
        <FullProfile uid={u.uid} />
      </div>
      <div className="md:col-span-3 border-t border-white/5 pt-4">
        <ActionBar u={u} perms={perms} isMain={isMain} onRefresh={onRefresh} />
      </div>
    </div>
  );
}

export default function UsersManager() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [diag, setDiag] = useState("");
  const [role, setRole] = useState("");
  const [isMain, setIsMain] = useState(false);
  const [showAllocate, setShowAllocate] = useState(false);
  const [perms, setPerms] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [open, setOpen] = useState(null); // uid expanded
  const debounce = useRef(null);
  const seq = useRef(0);

  const load = async (search) => {
    const my = ++seq.current;
    setLoading(true); setErr("");
    try {
      const { data } = await staffApi.get("/admin/users", { params: search ? { q: search } : {} });
      if (my !== seq.current) return;   // a newer search already answered
      setRows(data.users || []);
      setRole(data.role || "");
      setIsMain(Boolean(data.is_main));
    } catch (e) {
      if (my !== seq.current) return;
      setErr(e?.response?.data?.detail || "Could not load users.");
      try {
        const { data } = await staffApi.get("/admin/whoami");
        if (data?.reason) setDiag(data.reason);
      } catch (_) { /* diagnostics unavailable */ }
    } finally { if (my === seq.current) setLoading(false); }
  };

  useEffect(() => {
    adminOps.permissions().then((d) => setPerms(d.permissions || [])).catch(() => setPerms([]));
  }, []);

  const refresh = () => { load(q); setRefreshKey((k) => k + 1); };

  // Real-time search (debounced server call).
  useEffect(() => {
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(() => load(q), 300);
    return () => debounce.current && clearTimeout(debounce.current);
    // eslint-disable-next-line
  }, [q]);

  const counts = useMemo(() => {
    const c = { verified: 0, needs_review: 0, rejected: 0, not_applied: 0 };
    rows.forEach((r) => { c[r.status] = (c[r.status] || 0) + 1; });
    return c;
  }, [rows]);

  return (
    <div className="space-y-4" data-testid="admin-users-panel">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[280px] max-w-xl">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input data-testid="admin-users-search" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Search by email, mobile, User ID, company name…"
            className="glass rounded-xl pl-9 pr-4 py-3 outline-none w-full" />
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300" data-testid="count-verified">Verified {counts.verified}</span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300" data-testid="count-review">Review {counts.needs_review}</span>
          <span className="px-2.5 py-1 rounded-full bg-slate-500/15 text-slate-300" data-testid="count-notapplied">Not applied {counts.not_applied}</span>
        </div>
        <span className="text-xs text-slate-400 ml-auto" data-testid="admin-users-count">{rows.length} user{rows.length === 1 ? "" : "s"}</span>
        {isMain && (
          <button data-testid="open-allocate" onClick={() => setShowAllocate(true)}
            className="btn-primary !py-2 text-xs whitespace-nowrap"><UsersThree size={14} /> Allocate</button>
        )}
      </div>

      {showAllocate && <AllocatePanel onClose={() => setShowAllocate(false)} onAllocated={() => load(q)} />}

      {perms.includes("signoff.view") && <SignoffQueue key={`s${refreshKey}`} onDone={refresh} />}
      {perms.includes("users.delete") && <DeleteQueue key={`d${refreshKey}`} onDone={refresh} />}

      {err && (
        <div data-testid="admin-users-error" className="glass rounded-xl p-4 text-sm text-rose-300">
          {err}
          {diag && <div className="text-xs text-amber-200 mt-2" data-testid="admin-users-diagnosis">{diag}</div>}
        </div>
      )}

      <div className="glass-strong rounded-3xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-[10px] font-mono-display tracking-widest uppercase text-slate-400">
            <tr>
              <th className="text-left px-4 py-3">User ID</th>
              <th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3">Email</th>
              <th className="text-left px-4 py-3">Mobile</th>
              <th className="text-left px-4 py-3">Company</th>
              <th className="text-left px-4 py-3">Country</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <React.Fragment key={u.uid || u.email}>
                <tr data-testid="admin-user-row" className="border-t border-white/5 hover:bg-white/[0.02] cursor-pointer"
                  onClick={() => setOpen(open === u.uid ? null : u.uid)}>
                  <td className="px-4 py-3 font-mono-display text-cyan-300">{u.customer_id || "—"}</td>
                  <td className="px-4 py-3">{u.name || "—"}
                    {u.is_test_account && (
                      <span data-testid={`test-badge-${u.uid}`}
                        className="ml-2 text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-fuchsia-500/20 text-fuchsia-300">test</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs">{u.email || "—"}</td>
                  <td className="px-4 py-3 text-xs">{u.mobile || "—"}</td>
                  <td className="px-4 py-3 text-xs">{u.company_name || "—"}</td>
                  <td className="px-4 py-3 text-xs">{u.country || "—"}</td>
                  <td className="px-4 py-3"><StatusPill status={u.status} /></td>
                  <td className="px-4 py-3 text-right text-slate-400">
                    {open === u.uid ? <CaretUp size={14} /> : <CaretDown size={14} />}
                  </td>
                </tr>
                {open === u.uid && <tr><td colSpan={8} className="p-0"><UserDetail u={u} perms={perms} isMain={isMain} onRefresh={refresh} /></td></tr>}
              </React.Fragment>
            ))}
            {!loading && rows.length === 0 && !err && (
              <tr><td colSpan={8} className="px-4 py-10 text-center text-slate-500" data-testid="admin-users-empty">
                {role === "sub_admin" ? "No users have been allocated to you yet." : "No users found."}
              </td></tr>
            )}
            {loading && <tr><td colSpan={8} className="px-4 py-10 text-center text-slate-500">Loading users…</td></tr>}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-500">
        {role === "sub_admin"
          ? "You see only the users allocated to you. Approve/reject recommendations go to the main admin for final sign-off."
          : "Full platform visibility — everyone who has registered, whether or not they've applied for verification."}
      </p>
    </div>
  );
}
