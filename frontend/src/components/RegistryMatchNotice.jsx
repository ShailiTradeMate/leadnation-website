import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { ShieldCheck } from "@phosphor-icons/react";

export const RegistryMatchNotice = ({ refreshKey = "account" }) => {
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [err, setErr] = useState("");
  useEffect(() => { let live = true; api.post("/buyer-membership/check").then(r => { if (live) setData(r.data); }).catch(() => {}); return () => { live = false; }; }, [refreshKey]);
  if (!data?.match) return null;
  const accept = async () => {
    setBusy(true); setErr("");
    try { await api.post("/buyer-membership/accept"); setData(d => ({...d, status: "accepted"})); }
    catch (e) { setErr(e?.response?.data?.detail || "Could not confirm this match."); }
    finally { setBusy(false); }
  };
  return <section data-testid="registry-match-notice" className="border border-emerald-400/30 bg-emerald-500/10 rounded-lg p-4 my-5 text-sm">
    <h2 className="text-base font-semibold text-emerald-200 flex items-center gap-2"><ShieldCheck size={20} /> Welcome aboard — registry match found</h2>
    <p data-testid="registry-match-company" className="mt-2">Congratulations! Your details match {data.match.company_name} in our government-registry records.</p>
    <p className="text-slate-300 mt-2" data-testid="registry-kyc-status">{data.status === "needs_review" ? "Your selfie and company KYC are awaiting admin approval." : "Your company KYC and selfie still need approval before your account is authenticated as a Verified Buyer."}</p>
    {data.status === "candidate" && <button data-testid="registry-accept-match" onClick={accept} disabled={busy} className="btn-primary mt-3 !py-2">{busy ? "Confirming…" : "Continue with this company"}</button>}
    {data.status === "accepted" && <Link data-testid="registry-complete-kyc" to="/verify" className="btn-primary mt-3 !py-2">Complete KYC</Link>}
    {err && <p role="alert" data-testid="registry-match-error" className="text-rose-300 mt-2">{err}</p>}
  </section>;
};