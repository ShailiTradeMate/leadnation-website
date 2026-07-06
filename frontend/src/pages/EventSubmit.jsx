import React, { useEffect, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import SEO from "@/components/SEO";
import { api, submitEvent, uploadFile, fetchEventFilters, fetchEventPricing } from "@/lib/api";
import {
  UploadSimple, CircleNotch, CheckCircle, CreditCard, Image as ImageIcon,
  FileText, Buildings, Calendar, ArrowRight, X,
} from "@phosphor-icons/react";

const inputCls = "w-full glass rounded-xl px-4 py-3 outline-none text-white focus:border-cyan-400/40 text-sm bg-[#0a1024]";
const Label = ({ children, req }) => (
  <span className="text-[11px] font-mono-display tracking-widest uppercase text-slate-400">{children}{req && <span className="text-cyan-300"> *</span>}</span>
);

function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

export default function EventSubmit() {
  const [params] = useSearchParams();
  const [filters, setFilters] = useState({ categories: [], industries: [], audiences: [], countries: [] });
  const [pricing, setPricing] = useState(null);
  const [form, setForm] = useState({
    name: "", category: "Trade Fair", country: "India", city: "", venueName: "", venueAddress: "",
    startDate: "", endDate: "", organizer: "", description: "", audience: "All", industry: "Multi-sector",
    products: "", contactName: "", contactEmail: "", contactPhone: "", website: "",
    images: [], posters: [], flyers: [], documents: [],
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [paid, setPaid] = useState(null); // eventId when paid

  const setF = (patch) => setForm((p) => ({ ...p, ...patch }));

  useEffect(() => { fetchEventFilters().then(setFilters).catch(() => {}); }, []);
  useEffect(() => { fetchEventPricing({ country: form.country }).then(setPricing).catch(() => {}); }, [form.country]);

  // Handle Stripe return
  useEffect(() => {
    const eid = params.get("event_paid");
    const sid = params.get("session_id");
    if (eid && sid) {
      setBusy(true);
      const poll = async (n = 0) => {
        try {
          const { data } = await api.get(`/events/pay/stripe/status/${sid}`);
          if (data.status === "paid") { setPaid(data.eventId); setBusy(false); return; }
          if (data.status === "expired" || n > 6) { setErr("Payment not completed."); setBusy(false); return; }
        } catch (_) {}
        setTimeout(() => poll(n + 1), 2000);
      };
      poll();
    }
  }, [params]);

  const priceLabel = pricing ? `${pricing.symbol}${Number(pricing.amount).toLocaleString()} / ${pricing.durationDays} days` : "…";

  const onUpload = async (field, files) => {
    if (!files?.length) return;
    setBusy(true); setErr("");
    try {
      const urls = [...form[field]];
      for (const file of Array.from(files)) {
        const fd = new FormData(); fd.append("file", file);
        const res = await uploadFile(fd);
        urls.push({ url: res.url, name: res.filename });
      }
      setF({ [field]: urls });
    } catch (e) { setErr("Upload failed — file must be under 12MB."); }
    finally { setBusy(false); }
  };
  const removeFile = (field, idx) => setF({ [field]: form[field].filter((_, i) => i !== idx) });

  const validate = () => {
    if (!form.name.trim()) return "Event name is required.";
    if (!form.country) return "Country is required.";
    if (!form.contactEmail.includes("@")) return "A valid contact email is required.";
    if (!form.startDate) return "Start date is required.";
    return "";
  };

  const submitAndPay = async () => {
    const v = validate();
    if (v) { setErr(v); return; }
    setBusy(true); setErr("");
    try {
      const payload = {
        ...form,
        images: form.images.map((x) => x.url),
        posters: form.posters.map((x) => x.url),
        flyers: form.flyers.map((x) => x.url),
        documents: form.documents.map((x) => x.url),
      };
      const sub = await submitEvent(payload);
      const eid = sub.eventId;
      if (pricing?.gateway === "razorpay") {
        const ok = await loadRazorpay();
        if (!ok) { setErr("Could not load payment. Try again."); setBusy(false); return; }
        const { data: order } = await api.post(`/events/${eid}/pay/razorpay/order`);
        const rzp = new window.Razorpay({
          key: order.keyId, amount: order.amount, currency: order.currency,
          name: "LeadNation", description: `Event listing: ${order.eventName}`, order_id: order.orderId,
          prefill: { name: order.contact?.name, email: order.contact?.email, contact: order.contact?.phone },
          theme: { color: "#00C2FF" },
          handler: async (r) => {
            try {
              await api.post("/events/pay/razorpay/verify", {
                razorpay_order_id: r.razorpay_order_id, razorpay_payment_id: r.razorpay_payment_id,
                razorpay_signature: r.razorpay_signature });
              setPaid(eid);
            } catch (_) { setErr("Payment verification failed."); }
            setBusy(false);
          },
          modal: { ondismiss: () => setBusy(false) },
        });
        rzp.open();
      } else {
        const { data } = await api.post(`/events/${eid}/pay/stripe`, { origin: window.location.origin });
        window.location.href = data.url;
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not submit event. Please try again.");
      setBusy(false);
    }
  };

  if (paid) {
    return (
      <>
        <SEO title="Event submitted · LeadNation" path="/expo/submit" />
        <section className="max-w-2xl mx-auto px-6 pt-32 pb-24 text-center">
          <CheckCircle size={56} weight="duotone" className="text-emerald-300 mx-auto" />
          <h1 className="font-display font-extrabold text-3xl mt-4">Payment received 🎉</h1>
          <p className="text-slate-300 mt-3">Your event is now <b>under admin review</b>. You'll get an email at every step — approval, publishing and expiry. Once approved it appears on the website and mobile app.</p>
          <div className="mt-6 flex gap-3 justify-center">
            <Link to="/expo" className="btn-primary">Back to Events</Link>
            <Link to="/expo/submit" className="btn-ghost" onClick={() => window.location.assign("/expo/submit")}>List another</Link>
          </div>
        </section>
      </>
    );
  }

  return (
    <>
      <SEO title="List Your Trade Event · LeadNation Expo Engine" path="/expo/submit"
        description="Publish your trade fair, expo or business event to LeadNation's global network of exporters, importers and buyers — on web and mobile app." />
      <PageHero testIdPrefix="event-submit" label="Expo & Events Engine"
        title="List your event to the world."
        sub="Reach exporters, importers and buyers across the LeadNation web + app network. Submit your event, pay the listing fee, and go live after a quick admin review." />

      <section className="max-w-4xl mx-auto px-6 sm:px-10 pb-24">
        {/* Price banner */}
        <div className="glass-strong rounded-2xl p-5 mb-6 flex items-center justify-between flex-wrap gap-3" data-testid="event-price-banner">
          <div>
            <div className="text-[11px] font-mono-display tracking-widest uppercase text-cyan-300">Listing fee ({pricing?.region === "IN" ? "India" : "International"})</div>
            <div className="font-display font-extrabold text-2xl mt-1 text-gradient">{priceLabel}</div>
          </div>
          <div className="text-xs text-slate-400 max-w-xs">Fee depends on your event's country. Paid via {pricing?.gateway === "razorpay" ? "Razorpay" : "Stripe"}. Refund per our policy if not approved.</div>
        </div>

        <div className="space-y-5">
          {/* Details */}
          <Card icon={Calendar} title="Event details">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label={<Label req>Event name</Label>}><input data-testid="ev-name" className={inputCls} value={form.name} onChange={(e) => setF({ name: e.target.value })} placeholder="e.g. India Global Export Summit" /></Field>
              <Field label={<Label req>Category</Label>}>
                <select data-testid="ev-category" className={inputCls} value={form.category} onChange={(e) => setF({ category: e.target.value })}>
                  {filters.categories.map((c) => <option key={c} className="bg-[#0a1024]">{c}</option>)}
                </select>
              </Field>
              <Field label={<Label req>Country</Label>}>
                <select data-testid="ev-country" className={inputCls} value={form.country} onChange={(e) => setF({ country: e.target.value })}>
                  {["India", "UAE", "USA", "United Kingdom", "Germany", "Singapore", "China", "Australia", "Saudi Arabia", "Other"].map((c) => <option key={c} className="bg-[#0a1024]">{c}</option>)}
                </select>
              </Field>
              <Field label={<Label>City</Label>}><input data-testid="ev-city" className={inputCls} value={form.city} onChange={(e) => setF({ city: e.target.value })} /></Field>
              <Field label={<Label req>Start date</Label>}><input data-testid="ev-start" type="date" className={inputCls} value={form.startDate} onChange={(e) => setF({ startDate: e.target.value })} /></Field>
              <Field label={<Label>End date</Label>}><input data-testid="ev-end" type="date" className={inputCls} value={form.endDate} onChange={(e) => setF({ endDate: e.target.value })} /></Field>
              <Field label={<Label>Industry</Label>}>
                <select data-testid="ev-industry" className={inputCls} value={form.industry} onChange={(e) => setF({ industry: e.target.value })}>
                  {filters.industries.map((c) => <option key={c} className="bg-[#0a1024]">{c}</option>)}
                </select>
              </Field>
              <Field label={<Label>Target audience</Label>}>
                <select data-testid="ev-audience" className={inputCls} value={form.audience} onChange={(e) => setF({ audience: e.target.value })}>
                  {filters.audiences.map((c) => <option key={c} className="bg-[#0a1024]">{c}</option>)}
                </select>
              </Field>
            </div>
            <Field label={<Label>Description / purpose of the venue</Label>}><textarea data-testid="ev-desc" rows={3} className={inputCls} value={form.description} onChange={(e) => setF({ description: e.target.value })} placeholder="What is this event about, who should attend, and what's on show?" /></Field>
            <Field label={<Label>Products covered</Label>}><input data-testid="ev-products" className={inputCls} value={form.products} onChange={(e) => setF({ products: e.target.value })} placeholder="e.g. Spices, Textiles, Machinery" /></Field>
          </Card>

          {/* Venue + organizer */}
          <Card icon={Buildings} title="Venue & organizer">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label={<Label>Venue name</Label>}><input data-testid="ev-venue" className={inputCls} value={form.venueName} onChange={(e) => setF({ venueName: e.target.value })} /></Field>
              <Field label={<Label>Organizer</Label>}><input data-testid="ev-organizer" className={inputCls} value={form.organizer} onChange={(e) => setF({ organizer: e.target.value })} /></Field>
              <Field label={<Label>Venue address</Label>}><input data-testid="ev-address" className={inputCls} value={form.venueAddress} onChange={(e) => setF({ venueAddress: e.target.value })} /></Field>
              <Field label={<Label>Event website</Label>}><input data-testid="ev-website" className={inputCls} value={form.website} onChange={(e) => setF({ website: e.target.value })} placeholder="https://" /></Field>
            </div>
          </Card>

          {/* Contact */}
          <Card icon={FileText} title="Contact details">
            <div className="grid sm:grid-cols-3 gap-4">
              <Field label={<Label>Contact name</Label>}><input data-testid="ev-contact-name" className={inputCls} value={form.contactName} onChange={(e) => setF({ contactName: e.target.value })} /></Field>
              <Field label={<Label req>Contact email</Label>}><input data-testid="ev-contact-email" className={inputCls} value={form.contactEmail} onChange={(e) => setF({ contactEmail: e.target.value })} placeholder="you@company.com" /></Field>
              <Field label={<Label>Contact phone</Label>}><input data-testid="ev-contact-phone" className={inputCls} value={form.contactPhone} onChange={(e) => setF({ contactPhone: e.target.value })} /></Field>
            </div>
          </Card>

          {/* Media */}
          <Card icon={ImageIcon} title="Venue photo, posters, flyers & documents">
            <div className="grid sm:grid-cols-2 gap-4">
              <Uploader label="Venue / event images" field="images" accept="image/*" form={form} onUpload={onUpload} removeFile={removeFile} testid="ev-upload-images" />
              <Uploader label="Posters" field="posters" accept="image/*" form={form} onUpload={onUpload} removeFile={removeFile} testid="ev-upload-posters" />
              <Uploader label="Flyers" field="flyers" accept="image/*" form={form} onUpload={onUpload} removeFile={removeFile} testid="ev-upload-flyers" />
              <Uploader label="Documents (PDF)" field="documents" accept=".pdf,image/*" form={form} onUpload={onUpload} removeFile={removeFile} testid="ev-upload-docs" />
            </div>
          </Card>

          {err && <div data-testid="event-submit-error" className="text-rose-300 text-sm glass rounded-xl px-4 py-3">{err}</div>}

          <button data-testid="event-submit-pay" onClick={submitAndPay} disabled={busy} className="btn-primary w-full justify-center disabled:opacity-50">
            {busy ? <><CircleNotch size={18} className="animate-spin" /> Processing…</> : <><CreditCard size={18} weight="bold" /> Submit & pay {priceLabel} <ArrowRight size={16} weight="bold" /></>}
          </button>
          <p className="text-[11px] text-slate-500 text-center">Your event goes live on web + app only after admin approval. You'll be emailed at every step.</p>
        </div>
      </section>
    </>
  );
}

const Card = ({ icon: Icon, title, children }) => (
  <div className="glass-strong rounded-3xl p-6 space-y-4">
    <div className="flex items-center gap-2 font-display font-bold text-lg"><Icon size={18} weight="duotone" className="text-cyan-300" />{title}</div>
    {children}
  </div>
);
const Field = ({ label, children }) => (<label className="block">{label}<div className="mt-1.5">{children}</div></label>);

function Uploader({ label, field, accept, form, onUpload, removeFile, testid }) {
  const ref = useRef();
  return (
    <div>
      <Label>{label}</Label>
      <div className="mt-1.5">
        <button type="button" data-testid={testid} onClick={() => ref.current?.click()}
          className="w-full glass rounded-xl px-4 py-3 text-sm text-slate-300 hover:border-cyan-400/40 flex items-center justify-center gap-2">
          <UploadSimple size={16} weight="bold" className="text-cyan-300" /> Upload {label.toLowerCase()}
        </button>
        <input ref={ref} type="file" accept={accept} multiple className="hidden" onChange={(e) => onUpload(field, e.target.files)} />
        {form[field].length > 0 && (
          <div className="mt-2 space-y-1">
            {form[field].map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-xs glass rounded-lg px-3 py-1.5">
                <FileText size={12} className="text-cyan-300 shrink-0" />
                <span className="truncate flex-1">{f.name}</span>
                <button onClick={() => removeFile(field, i)} className="text-rose-300"><X size={12} /></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
