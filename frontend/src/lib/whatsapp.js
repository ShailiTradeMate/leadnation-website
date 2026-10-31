import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { CONTACT } from "@/data/contact";
import { useAuth } from "@/lib/AuthContext";

// Message templates live in the backend (admin-editable). These are the offline
// fallbacks and must mirror backend/wa_templates.py DEFAULTS.
export const WA_DEFAULTS = {
  general:
    "Hi Vametra AI, I'm reaching out to understand how Vametra AI can help my trade business.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n\nPage I'm on: {{page}}",
  service_request:
    "Hi Vametra AI, I have just submitted a service request for {{service}} on your website and I'd like to take it forward here on WhatsApp.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n• Request ID: {{request_id}}\n\nPlease confirm the next steps and the documents you need from me.",
  service_enquiry:
    "Hi Vametra AI, I'm interested in your {{service}} service and I want to know the charges, documents required and how long it takes.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}",
  contact:
    "Hi Vametra AI, I'm reaching out through your Contact page because I need help with my import-export requirement.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n\nWhat I need help with: ",
  supplier_connect:
    "Hi Vametra AI, please connect me with the supplier {{company}} ({{product}}) listed on your website.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n\nQuantity / requirement: ",
  cha_connect:
    "Hi Vametra AI, please connect me with the CHA {{cha}} at {{port}} port.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n\nShipment details: ",
  tool_help:
    "Hi Vametra AI, I'm using the {{tool}} on your website and I need help understanding the result for my shipment.\n\nMy details\n• Name: {{name}}\n• Vametra ID: {{customer_id}}\n• Mobile: {{phone}}\n• Email: {{email}}\n\nPage I'm on: {{page}}",
  ca_message:
    "Hi {{name}}, this is {{ca_name}} from Vametra AI regarding your {{service}} request (ID {{request_id}}).\n\n{{message}}\n\n{{documents}}\n\nThe same has been emailed to {{email}}. Reply here if you need anything else.",
};

// Signed-out visitors fill these in themselves; everything else is dropped when empty.
const ASK_USER = ["name", "phone"];
const BLANK = "______";

// href -> { key, vars } for every link built through waLink, so the global click
// logger knows which entry point the customer tapped.
const linkMeta = new Map();

let cache = null;
let inflight = null;
export function loadWaTemplates() {
  if (cache) return Promise.resolve(cache);
  if (!inflight) {
    inflight = api
      .get("/whatsapp/templates")
      .then((r) => { cache = { ...WA_DEFAULTS, ...(r.data?.templates || {}) }; return cache; })
      .catch(() => WA_DEFAULTS);
  }
  return inflight;
}

export function renderWaMessage(tpl, vars = {}) {
  return tpl
    .split("\n")
    .map((line) => {
      const keys = [...line.matchAll(/\{\{(\w+)\}\}/g)].map((m) => m[1]);
      const filled = keys.filter((k) => vars[k]);
      // Drop a detail line we cannot fill and should not ask for (e.g. Vametra ID).
      if (keys.length && !filled.length && !keys.some((k) => ASK_USER.includes(k))) return null;
      return line.replace(/\{\{(\w+)\}\}/g, (_, k) => (vars[k] ? String(vars[k]) : BLANK));
    })
    .filter((l) => l !== null)
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function waNumber() {
  return CONTACT.whatsapp.replace(/\D/g, "");
}

// Customer numbers typed on forms: "98765 43210" -> "919876543210".
export function normalizePhone(p) {
  let d = String(p || "").replace(/\D/g, "").replace(/^0+/, "");
  if (d.startsWith("00")) d = d.slice(2);
  if (d.length === 10) d = "91" + d;
  return d.length >= 11 ? d : "";
}

export function waLinkTo(phoneDigits, message) {
  return `https://wa.me/${phoneDigits}?text=${encodeURIComponent(message)}`;
}

function identityFrom(auth) {
  const user = auth.account?.user || {};
  const profile = auth.account?.profile || {};
  return {
    name: user.full_name || profile.name || "",
    customer_id: user.customer_id || "",
    email: user.email || profile.email || "",
    phone: profile.mobile || profile.phone || user.mobile || user.phone || "",
  };
}

async function postClick(payload) {
  let headers = { "Content-Type": "application/json" };
  try {
    const { auth } = await import("@/lib/firebase");
    if (auth.currentUser) headers.Authorization = `Bearer ${await auth.currentUser.getIdToken()}`;
  } catch (_) { /* guest */ }
  fetch(`${process.env.REACT_APP_BACKEND_URL}/api/whatsapp/clicks`, { method: "POST", keepalive: true, headers, body: JSON.stringify(payload) }).catch(() => {});
}

// Mounted once in Layout: records every tap on a wa.me link against the customer
// so the CA sees it in the request drawer.
export function useWaClickLogging(enabled = true) {
  const auth = useAuth() || {};
  const identity = identityFrom(auth);
  const ref = useRef(identity);
  ref.current = identity;
  useEffect(() => {
    if (!enabled) return undefined;
    const onClick = (e) => {
      const a = e.target?.closest?.('a[href*="wa.me/"], a[href*="whatsapp.com/"]');
      if (!a) return;
      const href = a.getAttribute("href") || "";
      const meta = linkMeta.get(href) || { key: "direct", vars: {} };
      let message = "";
      try { message = new URL(href).searchParams.get("text") || ""; } catch (_) { /* ignore */ }
      const id = ref.current;
      const v = meta.vars || {};
      postClick({
        key: meta.key, page: window.location.pathname + window.location.search, message,
        requestId: v.request_id || null, service: v.service || null,
        name: id.name || v.name || null, phone: id.phone || v.phone || null,
        email: id.email || v.email || null, customerId: id.customer_id || null,
      });
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, [enabled]);
}

export function useWhatsApp() {
  const auth = useAuth() || {};
  const [templates, setTemplates] = useState(cache || WA_DEFAULTS);
  useEffect(() => { loadWaTemplates().then(setTemplates); }, []);

  const identity = identityFrom(auth);

  const waMessage = (key, vars = {}) =>
    renderWaMessage(templates[key] || WA_DEFAULTS[key] || WA_DEFAULTS.general, {
      ...identity,
      page: typeof window !== "undefined" ? window.location.href : "",
      ...vars,
    });

  const waLink = (key, vars = {}) => {
    const url = `https://wa.me/${waNumber()}?text=${encodeURIComponent(waMessage(key, vars))}`;
    linkMeta.set(url, { key, vars });
    return url;
  };

  return { waLink, waMessage };
}
