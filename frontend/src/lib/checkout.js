import { api } from "@/lib/api";

// Loads Razorpay Checkout.js once.
function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => reject(new Error("Failed to load Razorpay"));
    document.body.appendChild(s);
  });
}

// Unified checkout for subscriptions / reports / downloads / events.
// Picks the region's gateway: Razorpay (IN, when keys are configured) or Stripe.
// Both gateways funnel back to the SAME /account success URL so all post-payment
// logic (subscription activation, PDF download record) stays in one place.
// NOTE: professional services (GST/IEC) never use this — they are enquiry-based.
export async function startCheckout({ kind, region, projectId = "", email = "", name = "", headers = {} }) {
  const origin = window.location.origin;
  const cfg = { headers };

  let gateway = "stripe";
  try {
    const { data } = await api.get("/payments/pricing", { params: { region } });
    gateway = data.gateway || "stripe";
  } catch (_) {}

  if (gateway !== "razorpay") {
    const { data } = await api.post("/payments/checkout", { kind, region, projectId, origin, email, name }, cfg);
    window.location.href = data.url;
    return true;
  }

  const { data: order } = await api.post(
    "/payments/razorpay/order", { kind, region, projectId, origin, email, name }, cfg);
  await loadRazorpayScript();

  const isSub = ["monthly", "annual", "subscription"].includes(kind);
  const successUrl = `${origin}/account?tab=${isSub ? "billing" : "downloads"}&session_id=${order.order_id}&pid=${projectId || ""}`;

  return await new Promise((resolve) => {
    const rzp = new window.Razorpay({
      key: order.key_id,
      amount: order.amount,        // paise (server-computed)
      currency: order.currency,
      name: order.name,
      description: order.description,
      order_id: order.order_id,
      prefill: order.prefill || {},
      theme: { color: "#22d3ee" },
      handler: async (resp) => {
        try {
          await api.post("/payments/razorpay/verify", {
            razorpay_payment_id: resp.razorpay_payment_id,
            razorpay_order_id: resp.razorpay_order_id,
            razorpay_signature: resp.razorpay_signature,
          }, cfg);
        } catch (_) {}
        window.location.href = successUrl;
        resolve(true);
      },
      modal: { ondismiss: () => resolve(false) },
    });
    rzp.open();
  });
}
