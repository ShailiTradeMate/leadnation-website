import React from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Globe, Compass, Newspaper, CalendarBlank, Package, Phone, List, X,
  GraduationCap, Calculator, ChartLine, MapPin, CaretDown,
} from "@phosphor-icons/react";

const PRIMARY = [
  { to: "/", label: "Home", icon: Globe },
  { to: "/customs-compliance", label: "Customs", icon: Compass },
  { to: "/product-info", label: "Products", icon: Package },
  { to: "/expo", label: "Expos", icon: CalendarBlank },
  { to: "/trade-news", label: "News", icon: Newspaper },
];

const TOOLS = [
  { to: "/tools/duty-calculator", label: "Duty Calculator", icon: Calculator, desc: "Free customs & tax estimator" },
  { to: "/intelligence", label: "Intelligence Hub", icon: ChartLine, desc: "Gold, oil, FX & trends" },
  { to: "/academy", label: "Academy", icon: GraduationCap, desc: "Free trade courses" },
  { to: "/countries", label: "Country Profiles", icon: MapPin, desc: "India, UAE, USA + 250 more" },
];

export default function Nav({ active = "/" }) {
  const [open, setOpen] = React.useState(false);
  const [toolsOpen, setToolsOpen] = React.useState(false);
  const navigate = useNavigate();

  return (
    <header className="fixed top-0 inset-x-0 z-50">
      <div className="glass-strong">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 h-[68px] flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group" data-testid="nav-logo-link">
            <LogoMark />
            <div className="leading-none">
              <div className="text-[15px] font-display font-extrabold tracking-tight">LeadNation</div>
              <div className="text-[10px] font-mono-display tracking-[0.25em] text-cyan-300/80 uppercase mt-0.5">
                Trade Intelligence
              </div>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-1">
            {PRIMARY.map((l) => {
              const Icon = l.icon;
              const isActive = active === l.to;
              return (
                <Link key={l.to} to={l.to}
                  data-testid={`nav-link-${l.label.toLowerCase()}`}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-full text-[13px] font-medium transition-all ${
                    isActive ? "tab-active text-white" : "text-slate-300 hover:text-white hover:bg-white/5"
                  }`}>
                  <Icon size={15} weight="duotone" />
                  {l.label}
                </Link>
              );
            })}

            {/* Tools dropdown */}
            <div className="relative" onMouseEnter={() => setToolsOpen(true)} onMouseLeave={() => setToolsOpen(false)}>
              <button
                data-testid="nav-tools-toggle"
                className={`flex items-center gap-2 px-3.5 py-2 rounded-full text-[13px] font-medium transition-all ${
                  TOOLS.some(t => active === t.to) ? "tab-active text-white" : "text-slate-300 hover:text-white hover:bg-white/5"
                }`}
              >
                <Calculator size={15} weight="duotone" />
                Tools
                <CaretDown size={11} className={`transition-transform ${toolsOpen ? "rotate-180" : ""}`} />
              </button>
              {toolsOpen && (
                <div className="absolute top-full right-0 pt-3 w-[330px]">
                  <div className="glass-strong rounded-2xl p-3 border border-white/10 shadow-2xl">
                    {TOOLS.map((t) => {
                      const Icon = t.icon;
                      return (
                        <Link key={t.to} to={t.to}
                          data-testid={`nav-tools-${t.label.toLowerCase().replace(/\s+/g, "-")}`}
                          className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5">
                          <div className="w-9 h-9 rounded-lg grid place-items-center bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-white/10 shrink-0">
                            <Icon size={16} weight="duotone" className="text-cyan-300" />
                          </div>
                          <div>
                            <div className="text-sm font-semibold">{t.label}</div>
                            <div className="text-[11px] text-slate-400">{t.desc}</div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <Link to="/contact"
              data-testid="nav-link-contact"
              className={`flex items-center gap-2 px-3.5 py-2 rounded-full text-[13px] font-medium transition-all ${
                active === "/contact" ? "tab-active text-white" : "text-slate-300 hover:text-white hover:bg-white/5"
              }`}>
              <Phone size={15} weight="duotone" />
              Contact
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <button data-testid="nav-cta-create-account" onClick={() => navigate("/contact")}
              className="hidden sm:inline-flex btn-ghost !py-2.5 !px-5 text-[13px]">
              Create Account
            </button>
            <button data-testid="nav-cta-download" onClick={() => navigate("/#download")}
              className="btn-primary !py-2.5 !px-5 text-[13px]">
              Download App
            </button>
            <button data-testid="nav-mobile-toggle" className="lg:hidden text-white p-2" onClick={() => setOpen(!open)}>
              {open ? <X size={22} /> : <List size={22} />}
            </button>
          </div>
        </div>

        {open && (
          <div className="lg:hidden border-t border-white/5">
            <div className="px-5 py-4 grid gap-1">
              {[...PRIMARY, ...TOOLS, { to: "/contact", label: "Contact", icon: Phone }].map((l) => {
                const Icon = l.icon;
                return (
                  <Link key={l.to} to={l.to} onClick={() => setOpen(false)}
                    data-testid={`nav-mobile-link-${l.label.toLowerCase().replace(/\s+/g, "-")}`}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-200 hover:bg-white/5">
                    <Icon size={18} weight="duotone" />
                    {l.label}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export function LogoMark({ size = 36 }) {
  return (
    <div className="relative shrink-0 grid place-items-center rounded-xl" style={{ width: size, height: size }}>
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-cyan-400/40 via-violet-500/30 to-transparent blur-md" />
      <svg viewBox="0 0 40 40" width={size} height={size} className="relative">
        <defs>
          <linearGradient id="lg" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#00C2FF" />
            <stop offset="100%" stopColor="#7C3AED" />
          </linearGradient>
        </defs>
        <circle cx="20" cy="20" r="14" fill="none" stroke="url(#lg)" strokeWidth="1.5" />
        <ellipse cx="20" cy="20" rx="14" ry="5.5" fill="none" stroke="url(#lg)" strokeWidth="1" opacity=".6" />
        <ellipse cx="20" cy="20" rx="5.5" ry="14" fill="none" stroke="url(#lg)" strokeWidth="1" opacity=".6" />
        <circle cx="20" cy="20" r="2.5" fill="url(#lg)" />
        <circle cx="30" cy="13" r="1.5" fill="#00C2FF" />
        <circle cx="11" cy="27" r="1.5" fill="#7C3AED" />
      </svg>
    </div>
  );
}
