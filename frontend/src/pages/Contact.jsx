import React, { useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { CONTACT } from "@/data/contact";
import { createLead } from "@/lib/api";
import {
  EnvelopeSimple,
  WhatsappLogo,
  MapPin,
  InstagramLogo,
  PaperPlaneTilt,
  CheckCircle,
} from "@phosphor-icons/react";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", phone: "", country: "", message: "" });
  const [status, setStatus] = useState("idle"); // idle | submitting | done | error
  const [errorMsg, setErrorMsg] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus("submitting");
    setErrorMsg("");
    try {
      await createLead({ ...form, source: "contact-page" });
      setStatus("done");
      setForm({ name: "", email: "", phone: "", country: "", message: "" });
    } catch (err) {
      setStatus("error");
      setErrorMsg("Something went wrong. Please WhatsApp us or try again.");
    }
  };

  const waHref = `https://wa.me/${CONTACT.whatsapp.replace(/\D/g, "")}`;
  const mapSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${CONTACT.lng - 0.01}%2C${CONTACT.lat - 0.005}%2C${CONTACT.lng + 0.01}%2C${CONTACT.lat + 0.005}&layer=mapnik&marker=${CONTACT.lat}%2C${CONTACT.lng}`;

  return (
    <>
      <SEO
        title="Contact LeadNation · WhatsApp, Email & HQ"
        description="Reach LeadNation on WhatsApp +91 82371 61088, email admin@leadnation.app, or visit our HQ in Ahilyanagar, Maharashtra, India."
        path="/contact"
        keywords="LeadNation contact, LeadNation WhatsApp, LeadNation email, Ahilyanagar office, LeadNation HQ"
      />
      <PageHero
        testIdPrefix="contact"
        label="Contact · Create Account"
        title="Let's put your trade on autopilot."
        sub="Reach the LeadNation team on email, WhatsApp or Instagram — we usually reply within a few hours."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-2 gap-8">
        {/* Form */}
        <form onSubmit={onSubmit} className="glass-strong rounded-3xl p-7 sm:p-9 space-y-4">
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
            Create an account / Reach out
          </div>
          <h2 className="font-display font-extrabold text-2xl sm:text-3xl">Start your trade journey</h2>

          <div className="grid sm:grid-cols-2 gap-4">
            <Input label="Full name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required testId="contact-name" />
            <Input label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required testId="contact-email" />
            <Input label="Phone / WhatsApp" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} testId="contact-phone" />
            <Input label="Country" value={form.country} onChange={(v) => setForm({ ...form, country: v })} testId="contact-country" />
          </div>
          <Textarea label="How can we help?" value={form.message} onChange={(v) => setForm({ ...form, message: v })} testId="contact-message" />

          <button
            data-testid="contact-submit"
            className="btn-primary w-full justify-center"
            disabled={status === "submitting"}
          >
            {status === "submitting" ? "Sending…" : <>Create my account <PaperPlaneTilt size={16} weight="bold" /></>}
          </button>

          {status === "done" && (
            <div data-testid="contact-success" className="flex items-center gap-2 text-sm text-emerald-300">
              <CheckCircle size={16} weight="fill" /> Thanks — we'll be in touch shortly.
            </div>
          )}
          {status === "error" && (
            <div data-testid="contact-error" className="text-sm text-rose-300">{errorMsg}</div>
          )}
        </form>

        {/* Contact details */}
        <div className="space-y-4">
          <ContactRow
            Icon={EnvelopeSimple}
            label="Email"
            value={CONTACT.email}
            href={`mailto:${CONTACT.email}`}
            testId="contact-info-email"
          />
          <ContactRow
            Icon={WhatsappLogo}
            label="WhatsApp"
            value={CONTACT.whatsappDisplay}
            href={waHref}
            external
            accent="#25D366"
            testId="contact-info-whatsapp"
          />
          <ContactRow
            Icon={InstagramLogo}
            label="Instagram"
            value={`@${CONTACT.instagram}`}
            href={CONTACT.instagramUrl}
            external
            testId="contact-info-instagram"
          />
          <ContactRow
            Icon={MapPin}
            label="Office"
            value={CONTACT.address}
            testId="contact-info-address"
          />

          {/* Map */}
          <div className="glass-strong rounded-3xl overflow-hidden border border-white/5">
            <div className="px-5 py-4 flex items-center gap-2 border-b border-white/5">
              <MapPin size={16} className="text-cyan-300" weight="duotone" />
              <div className="text-xs font-mono-display tracking-[0.25em] uppercase text-cyan-300">
                Ahilyanagar · India
              </div>
            </div>
            <iframe
              title="LeadNation HQ"
              data-testid="contact-map"
              src={mapSrc}
              className="w-full h-[320px]"
              style={{ filter: "invert(0.92) hue-rotate(180deg) brightness(0.95) contrast(0.95)" }}
              loading="lazy"
            />
            <div className="px-5 py-3 flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono-display tracking-widest">{CONTACT.lat.toFixed(5)}, {CONTACT.lng.toFixed(5)}</span>
              <a
                target="_blank" rel="noopener noreferrer"
                href={`https://www.google.com/maps?q=${CONTACT.lat},${CONTACT.lng}`}
                data-testid="contact-map-open"
                className="text-cyan-300 hover:underline"
              >Open in Google Maps</a>
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}

function Input({ label, value, onChange, type = "text", required, testId }) {
  return (
    <label className="block">
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}{required && " *"}</div>
      <input
        data-testid={testId}
        type={type}
        value={value}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        className="w-full glass rounded-xl px-4 py-3 outline-none text-white placeholder:text-slate-500"
      />
    </label>
  );
}
function Textarea({ label, value, onChange, testId }) {
  return (
    <label className="block">
      <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400 mb-2">{label}</div>
      <textarea
        data-testid={testId}
        value={value}
        rows={4}
        onChange={(e) => onChange(e.target.value)}
        className="w-full glass rounded-xl px-4 py-3 outline-none text-white placeholder:text-slate-500"
      />
    </label>
  );
}
function ContactRow({ Icon, label, value, href, external, accent, testId }) {
  const Content = (
    <div className="glass rounded-2xl p-5 flex items-start gap-4 hover:border-cyan-400/30 transition-all">
      <div
        className="w-11 h-11 rounded-xl grid place-items-center shrink-0"
        style={{ background: accent ? `${accent}22` : "rgba(0,194,255,0.12)", border: `1px solid ${accent || "rgba(0,194,255,0.25)"}` }}
      >
        <Icon size={20} weight="duotone" color={accent || "#00C2FF"} />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] font-mono-display tracking-[0.25em] uppercase text-slate-400">{label}</div>
        <div className="mt-1 text-white text-sm break-words">{value}</div>
      </div>
    </div>
  );
  if (!href) return <div data-testid={testId}>{Content}</div>;
  return (
    <a data-testid={testId} href={href} target={external ? "_blank" : undefined} rel={external ? "noopener noreferrer" : undefined}>
      {Content}
    </a>
  );
}
