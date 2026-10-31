import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import { WhatsappLogo, FloppyDisk, ArrowCounterClockwise } from "@phosphor-icons/react";

export default function WhatsAppTemplatesManager() {
  const [items, setItems] = useState([]);
  const [placeholders, setPlaceholders] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [saving, setSaving] = useState("");
  const [msg, setMsg] = useState("");

  const load = () =>
    adminApi.get("/admin/whatsapp-templates").then((r) => {
      setItems(r.data.items || []);
      setPlaceholders(r.data.placeholders || []);
      setDrafts(Object.fromEntries((r.data.items || []).map((i) => [i.key, i.template])));
    });

  useEffect(() => { load().catch(() => setMsg("Could not load templates.")); }, []);

  const save = async (key) => {
    setSaving(key); setMsg("");
    try {
      await adminApi.put(`/admin/whatsapp-templates/${key}`, { template: drafts[key] });
      await load();
      setMsg("Saved — live on the website.");
    } catch (_) { setMsg("Save failed."); }
    finally { setSaving(""); }
  };

  const reset = async (key) => {
    setSaving(key); setMsg("");
    try { await adminApi.post(`/admin/whatsapp-templates/${key}/reset`); await load(); setMsg("Reset to the default wording."); }
    catch (_) { setMsg("Reset failed."); }
    finally { setSaving(""); }
  };

  return (
    <div data-testid="wa-templates-manager">
      <div className="glass-strong rounded-3xl p-6">
        <div className="flex items-center gap-2 text-[#25D366]"><WhatsappLogo size={20} weight="fill" /><span className="font-display font-bold text-lg">WhatsApp message templates</span></div>
        <p className="text-sm text-slate-400 mt-2">
          These are the messages pre-filled in WhatsApp when a customer taps any chat button on the website.
          They are written in the customer's voice and auto-populate their details.
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {placeholders.map((p) => (
            <code key={p} data-testid={`wa-placeholder-${p}`} className="text-[11px] px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-cyan-200">{`{{${p}}}`}</code>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-2">A detail line is dropped automatically when we don't have that value; name and mobile stay as blanks for signed-out visitors to fill.</p>
        {msg && <div data-testid="wa-templates-msg" className="mt-3 text-sm text-emerald-300">{msg}</div>}
      </div>

      <div className="mt-5 grid gap-4">
        {items.map((it) => (
          <div key={it.key} data-testid={`wa-template-${it.key}`} className="glass rounded-3xl p-5">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="font-display font-bold">{it.label}</div>
                <div className="text-xs text-slate-400 mt-0.5">{it.where} · <code className="text-slate-500">{it.key}</code></div>
              </div>
              <div className="flex items-center gap-2">
                {it.customized && <span data-testid={`wa-template-customized-${it.key}`} className="text-[10px] uppercase tracking-widest text-amber-200 bg-amber-400/15 border border-amber-400/30 rounded-full px-2 py-1">Customised</span>}
                <button data-testid={`wa-template-save-${it.key}`} disabled={saving === it.key || drafts[it.key] === it.template}
                  onClick={() => save(it.key)} className="btn-primary !py-2 !px-3 text-xs disabled:opacity-40">
                  <FloppyDisk size={13} weight="bold" /> Save
                </button>
                <button data-testid={`wa-template-reset-${it.key}`} disabled={saving === it.key || !it.customized}
                  onClick={() => reset(it.key)} className="btn-ghost !py-2 !px-3 text-xs disabled:opacity-40">
                  <ArrowCounterClockwise size={13} weight="bold" /> Default
                </button>
              </div>
            </div>
            <textarea data-testid={`wa-template-input-${it.key}`} rows={9} value={drafts[it.key] ?? ""}
              onChange={(e) => setDrafts({ ...drafts, [it.key]: e.target.value })}
              className="mt-3 w-full glass rounded-2xl px-4 py-3 text-sm outline-none font-mono leading-relaxed" />
          </div>
        ))}
      </div>
    </div>
  );
}
