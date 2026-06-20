import React from "react";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import WhatsAppButton from "@/components/WhatsAppButton";
import { useLocation } from "react-router-dom";

export default function Layout({ children }) {
  const { pathname } = useLocation();
  return (
    <div className="relative min-h-screen bg-[#050816] text-white grain">
      <Nav active={pathname} />
      <main className="relative z-10 pt-[68px]">{children}</main>
      <Footer />
      <WhatsAppButton />
    </div>
  );
}
