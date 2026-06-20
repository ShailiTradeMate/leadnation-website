import React from "react";
import { CONTACT } from "@/data/contact";
import { WhatsappLogo } from "@phosphor-icons/react";
import { trackEvent } from "@/lib/analytics";

export default function WhatsAppButton() {
  const href = `https://wa.me/${CONTACT.whatsapp.replace(/\D/g, "")}?text=${encodeURIComponent(
    "Hi LeadNation team, I'd like to know more about the app."
  )}`;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => trackEvent("whatsapp_click", { location: "floating" })}
      data-testid="whatsapp-floating-btn"
      className="fixed bottom-6 right-6 z-[60] flex items-center gap-3 group"
      aria-label="Chat on WhatsApp"
    >
      <span className="hidden md:inline-flex glass px-3 py-2 rounded-full text-xs font-medium text-white/90 translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
        Chat with us
      </span>
      <span className="relative grid place-items-center w-14 h-14 rounded-full bg-[#25D366] shadow-[0_10px_40px_rgba(37,211,102,0.5)] group-hover:scale-110 transition-transform">
        <span className="absolute inset-0 rounded-full bg-[#25D366] animate-ping opacity-30" />
        <WhatsappLogo size={28} weight="fill" color="#fff" />
      </span>
    </a>
  );
}
