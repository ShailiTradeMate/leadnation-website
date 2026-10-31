import { useEffect, useState } from "react";
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
};

// Signed-out visitors fill these in themselves; everything else is dropped when empty.
const ASK_USER = ["name", "phone"];
const BLANK = "______";

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

export function useWhatsApp() {
  const auth = useAuth() || {};
  const [templates, setTemplates] = useState(cache || WA_DEFAULTS);
  useEffect(() => { loadWaTemplates().then(setTemplates); }, []);

  const user = auth.account?.user || {};
  const profile = auth.account?.profile || {};
  const identity = {
    name: user.full_name || profile.name || "",
    customer_id: user.customer_id || "",
    email: user.email || profile.email || "",
    phone: profile.mobile || profile.phone || "",
  };

  const waMessage = (key, vars = {}) =>
    renderWaMessage(templates[key] || WA_DEFAULTS[key] || WA_DEFAULTS.general, {
      ...identity,
      page: typeof window !== "undefined" ? window.location.href : "",
      ...vars,
    });

  const waLink = (key, vars = {}) =>
    `https://wa.me/${waNumber()}?text=${encodeURIComponent(waMessage(key, vars))}`;

  return { waLink, waMessage };
}
