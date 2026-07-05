import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Cookie, X } from "@phosphor-icons/react";
import { getConsent, setConsent } from "@/lib/analytics";

const Toggle = ({ on, onChange, disabled, testid }) => (
  <button type="button" disabled={disabled} onClick={() => onChange(!on)} data-testid={testid}
    className={`relative w-11 h-6 rounded-full transition-colors ${on ? "bg-cyan-400" : "bg-white/15"} ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}>
    <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${on ? "translate-x-5" : ""}`} />
  </button>
);

export default function CookieConsent() {
  const [show, setShow] = useState(false);
  const [manage, setManage] = useState(false);
  const [prefs, setPrefs] = useState({ analytics: true, marketing: true });

  useEffect(() => {
    if (!getConsent()) setShow(true);
    const open = () => {
      const c = getConsent();
      if (c) setPrefs({ analytics: !!c.analytics, marketing: !!c.marketing });
      setManage(true); setShow(true);
    };
    window.addEventListener("ln-open-cookie-prefs", open);
    return () => window.removeEventListener("ln-open-cookie-prefs", open);
  }, []);

  const acceptAll = () => { setConsent({ analytics: true, marketing: true }); setShow(false); setManage(false); };
  const rejectNonEssential = () => { setConsent({ analytics: false, marketing: false }); setShow(false); setManage(false); };
  const savePrefs = () => { setConsent(prefs); setShow(false); setManage(false); };

  if (!show) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-[100] p-3 sm:p-5 pointer-events-none" data-testid="cookie-consent">
      <div className="pointer-events-auto max-w-4xl mx-auto glass-strong rounded-2xl border border-white/10 shadow-2xl p-5 sm:p-6">
        {!manage ? (
          <div className="flex flex-col sm:flex-row items-start gap-4">
            <Cookie size={28} weight="duotone" className="text-cyan-300 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-slate-200">LeadNation uses cookies and analytics to improve your global trade experience.</p>
              <p className="text-xs text-slate-500 mt-1">Essential cookies keep you signed in and secure. Read our <Link to="/legal/cookies" className="text-cyan-300 hover:underline">Cookie Policy</Link> and <Link to="/legal/privacy" className="text-cyan-300 hover:underline">Privacy Policy</Link>.</p>
            </div>
            <div className="flex flex-wrap gap-2 shrink-0">
              <button data-testid="cookie-manage" onClick={() => setManage(true)} className="btn-ghost !py-2 !text-xs">Manage Preferences</button>
              <button data-testid="cookie-reject" onClick={rejectNonEssential} className="btn-ghost !py-2 !text-xs">Reject Non-Essential</button>
              <button data-testid="cookie-accept-all" onClick={acceptAll} className="btn-primary !py-2 !text-xs">Accept All</button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between">
              <div className="font-display font-bold text-lg flex items-center gap-2"><Cookie size={20} weight="duotone" className="text-cyan-300" /> Cookie Preferences</div>
              <button data-testid="cookie-close" onClick={() => (getConsent() ? setShow(false) : setManage(false))} className="text-slate-400 hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-3 mt-4">
              <div className="glass rounded-xl px-4 py-3 flex items-center justify-between">
                <div><div className="text-sm font-medium">Essential</div><div className="text-xs text-slate-500">Authentication, security & session. Always on.</div></div>
                <Toggle on disabled testid="cookie-essential-toggle" onChange={() => {}} />
              </div>
              <div className="glass rounded-xl px-4 py-3 flex items-center justify-between">
                <div><div className="text-sm font-medium">Analytics</div><div className="text-xs text-slate-500">Google Analytics 4, Google Tag Manager, Microsoft Clarity.</div></div>
                <Toggle on={prefs.analytics} testid="cookie-analytics-toggle" onChange={(v) => setPrefs((p) => ({ ...p, analytics: v }))} />
              </div>
              <div className="glass rounded-xl px-4 py-3 flex items-center justify-between">
                <div><div className="text-sm font-medium">Marketing</div><div className="text-xs text-slate-500">Meta Pixel & future advertising pixels.</div></div>
                <Toggle on={prefs.marketing} testid="cookie-marketing-toggle" onChange={(v) => setPrefs((p) => ({ ...p, marketing: v }))} />
              </div>
            </div>
            <div className="flex flex-wrap justify-end gap-2 mt-4">
              <button data-testid="cookie-reject-2" onClick={rejectNonEssential} className="btn-ghost !py-2 !text-xs">Reject Non-Essential</button>
              <button data-testid="cookie-save" onClick={savePrefs} className="btn-primary !py-2 !text-xs">Save Preferences</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
