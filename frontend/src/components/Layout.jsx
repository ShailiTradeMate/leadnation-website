import React from "react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import WhatsAppButton from "@/components/WhatsAppButton";
import BrainWidget from "@/components/BrainWidget";
import AnalyticsProvider from "@/components/Analytics";
import { useLocation } from "react-router-dom";

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const isAdmin = pathname.startsWith("/admin");
  return (
    <AnalyticsProvider>
      <div className="relative min-h-screen bg-[#050816] text-white grain">
        {!isAdmin && <Nav active={pathname} />}
        <main className={`relative z-10 ${isAdmin ? "" : "pt-[68px]"}`}>{children}</main>
        {!isAdmin && <Footer />}
        {!isAdmin && <WhatsAppButton />}
        {!isAdmin && <BrainWidget />}
      </div>
    </AnalyticsProvider>
  );
}
