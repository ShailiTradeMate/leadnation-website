import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft } from "@phosphor-icons/react";

export default function BackButton() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  if (pathname === "/" || pathname.startsWith("/admin")) return null;

  const goBack = () => {
    if (window.history.length > 2) navigate(-1);
    else navigate("/");
  };

  return (
    <button
      onClick={goBack}
      data-testid="global-back-btn"
      aria-label="Go back"
      className="fixed top-[80px] left-4 z-40 flex items-center gap-1.5 glass rounded-full pl-2.5 pr-3.5 py-2 text-xs font-medium text-slate-200 hover:text-cyan-300 hover:border-cyan-400/40 transition-all"
    >
      <ArrowLeft size={15} weight="bold" /> Back
    </button>
  );
}
