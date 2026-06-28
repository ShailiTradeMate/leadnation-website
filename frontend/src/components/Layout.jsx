import React from "react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import WhatsAppButton from "@/components/WhatsAppButton";
import BrainWidget from "@/components/BrainWidget";
import BackButton from "@/components/BackButton";
import AnalyticsProvider from "@/components/Analytics";
import { useLocation } from "react-router-dom";
import { SettingsProvider, useSettings } from "@/lib/SettingsContext";
import { Wrench } from "@phosphor-icons/react";

function Maintenance({ message }) {
  return (
    <section data-testid="maintenance-screen" className="min-h-screen grid place-items-center px-6 text-center">
      <div className="glass-strong rounded-3xl p-10 max-w-lg">
        <div className="w-14 h-14 mx-auto rounded-2xl grid place-items-center bg-gradient-to-br from-cyan-500/30 to-violet-500/30 border border-white/10">
          <Wrench size={26} weight="duotone" className="text-cyan-300" />
        </div>
        <h1 className="font-display font-extrabold text-3xl mt-5">Under Maintenance</h1>
        <p className="text-slate-400 mt-3">{message}</p>
      </div>
    </section>
  );
}

function Shell({ children }) {
  const { pathname } = useLocation();
  const { settings } = useSettings();
  const isAdmin = pathname.startsWith("/admin");
  const maintenance = settings.maintenance && !isAdmin;

  if (maintenance) {
    return (
      <div className="relative min-h-screen bg-[#050816] text-white grain">
        <Maintenance message={settings.maintenanceMessage} />
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-[#050816] text-white grain">
      {!isAdmin && <Nav active={pathname} />}
      {!isAdmin && <BackButton />}
      <main className={`relative z-10 ${isAdmin ? "" : "pt-[68px]"}`}>{children}</main>
      {!isAdmin && <Footer />}
      {!isAdmin && <WhatsAppButton />}
      {!isAdmin && <BrainWidget />}
    </div>
  );
}

export default function Layout({ children }) {
  return (
    <AnalyticsProvider>
      <SettingsProvider>
        <Shell>{children}</Shell>
      </SettingsProvider>
    </AnalyticsProvider>
  );
}
