import React from "react";
import { Link } from "react-router-dom";
import { CONTACT, APP_LINKS } from "@/data/contact";
import { openCookiePreferences } from "@/lib/analytics";
import { InstagramLogo, LinkedinLogo, WhatsappLogo, EnvelopeSimple, MapPin, AppleLogo, AndroidLogo } from "@phosphor-icons/react";
import { LogoMark } from "./Nav";
import { TAGLINE } from "@/lib/brand";

export default function Footer() {
  return (
    <footer className="relative mt-32 border-t border-white/5 bg-[#04050f]">
      <div className="max-w-7xl mx-auto px-6 sm:px-10 py-16 grid lg:grid-cols-4 gap-12">
        <div className="lg:col-span-2 max-w-md">
          <div className="flex items-center gap-3">
            <LogoMark size={42} />
            <div>
              <div className="font-display font-extrabold text-lg">LeadNation</div>
              <div className="text-[10px] font-mono-display tracking-[0.25em] text-cyan-300/80 uppercase">
                Global Trade Intelligence
              </div>
            </div>
          </div>
          <p className="mt-5 text-sm text-slate-400 leading-relaxed">
            The investor-grade portal that puts customs, compliance, expos and product
            intelligence in the hands of every trader — built for India, scaled for the world.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href={APP_LINKS.ios}
              data-testid="footer-download-ios"
              className="glass rounded-2xl px-4 py-3 flex items-center gap-3 hover:border-cyan-400/40 transition-all"
            >
              <AppleLogo size={26} weight="fill" />
              <div className="leading-tight">
                <div className="text-[10px] uppercase tracking-wider text-slate-400">Coming soon on</div>
                <div className="text-sm font-semibold">App Store</div>
              </div>
            </a>
            <a
              href={APP_LINKS.android}
              data-testid="footer-download-android"
              className="glass rounded-2xl px-4 py-3 flex items-center gap-3 hover:border-cyan-400/40 transition-all"
            >
              <AndroidLogo size={26} weight="fill" />
              <div className="leading-tight">
                <div className="text-[10px] uppercase tracking-wider text-slate-400">Coming soon on</div>
                <div className="text-sm font-semibold">Google Play</div>
              </div>
            </a>
          </div>
        </div>

        <div>
          <div className="text-xs font-mono-display tracking-[0.25em] text-cyan-300/80 uppercase mb-4">
            Explore
          </div>
          <ul className="space-y-2.5 text-sm text-slate-300">
            <li><Link to="/" className="hover:text-cyan-300" data-testid="footer-link-home">Home</Link></li>
            <li><Link to="/tools" className="hover:text-cyan-300" data-testid="footer-link-tools">Trade Tools Hub</Link></li>
            <li><Link to="/services" className="hover:text-cyan-300" data-testid="footer-link-services">Business Services</Link></li>
            <li><Link to="/brain" className="hover:text-cyan-300" data-testid="footer-link-ai">LeadNation Brain</Link></li>
            <li><Link to="/products" className="hover:text-cyan-300" data-testid="footer-link-products-index">Products</Link></li>
            <li><Link to="/corridors" className="hover:text-cyan-300" data-testid="footer-link-corridors">Trade Corridors</Link></li>
            <li><Link to="/countries" className="hover:text-cyan-300" data-testid="footer-link-countries">Country Profiles</Link></li>
            <li><Link to="/industries" className="hover:text-cyan-300" data-testid="footer-link-industries">Industries</Link></li>
            <li><Link to="/intelligence" className="hover:text-cyan-300" data-testid="footer-link-intelligence">Intelligence</Link></li>
            <li><Link to="/academy" className="hover:text-cyan-300" data-testid="footer-link-academy">Academy</Link></li>
            <li><Link to="/blog" className="hover:text-cyan-300" data-testid="footer-link-blog">Blog</Link></li>
            <li><Link to="/expo" className="hover:text-cyan-300" data-testid="footer-link-expo">Expos &amp; Events</Link></li>
            <li><Link to="/trade-news" className="hover:text-cyan-300" data-testid="footer-link-news">Trade News</Link></li>
            <li><Link to="/contact" className="hover:text-cyan-300" data-testid="footer-link-contact">Contact</Link></li>
          </ul>
        </div>

        <div>
          <div className="text-xs font-mono-display tracking-[0.25em] text-cyan-300/80 uppercase mb-4">
            Get in touch
          </div>
          <ul className="space-y-3 text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <EnvelopeSimple size={16} className="mt-1 text-cyan-300" />
              <a href={`mailto:${CONTACT.email}`} className="hover:text-cyan-300" data-testid="footer-email">{CONTACT.email}</a>
            </li>
            <li className="flex items-start gap-2">
              <WhatsappLogo size={16} className="mt-1 text-cyan-300" />
              <a href={`https://wa.me/${CONTACT.whatsapp.replace(/\D/g,"")}`} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-300" data-testid="footer-whatsapp">{CONTACT.whatsappDisplay}</a>
            </li>
            <li className="flex items-start gap-2">
              <InstagramLogo size={16} className="mt-1 text-cyan-300" />
              <a href={CONTACT.instagramUrl} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-300" data-testid="footer-instagram">@{CONTACT.instagram}</a>
            </li>
            <li className="flex items-start gap-2">
              <LinkedinLogo size={16} className="mt-1 text-cyan-300" />
              <a href={CONTACT.linkedinUrl} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-300" data-testid="footer-linkedin">LeadNation on LinkedIn</a>
            </li>
            <li className="flex items-start gap-2">
              <MapPin size={16} className="mt-1 text-cyan-300" />
              <span className="text-slate-400 leading-relaxed">{CONTACT.address}</span>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 sm:px-10 py-4 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-slate-500">
          <Link to="/legal/privacy" className="hover:text-cyan-300" data-testid="footer-link-privacy">Privacy Policy</Link>
          <Link to="/legal/terms" className="hover:text-cyan-300" data-testid="footer-link-terms">Terms of Service</Link>
          <Link to="/legal/cookies" className="hover:text-cyan-300" data-testid="footer-link-cookies">Cookie Policy</Link>
          <Link to="/legal/disclaimer" className="hover:text-cyan-300" data-testid="footer-link-disclaimer">Disclaimer</Link>
          <Link to="/legal/refund" className="hover:text-cyan-300" data-testid="footer-link-refund">Refund &amp; Cancellation</Link>
          <button onClick={() => openCookiePreferences()} className="hover:text-cyan-300" data-testid="footer-cookie-prefs">Cookie Preferences</button>
        </div>
      </div>
      <div className="border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6 sm:px-10 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div>© {new Date().getFullYear()} LeadNation · Vametra AI Technologies Pvt Ltd · All rights reserved.</div>
          <div className="font-mono-display tracking-widest">v1.0 · Built for global traders.</div>
        </div>
      </div>
    </footer>
  );
}
