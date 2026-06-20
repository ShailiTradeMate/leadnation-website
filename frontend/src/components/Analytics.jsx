import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { initAnalytics, trackPageView } from "@/lib/analytics";

export default function AnalyticsProvider({ children }) {
  const { pathname } = useLocation();
  useEffect(() => { initAnalytics(); }, []);
  useEffect(() => {
    trackPageView(pathname);
  }, [pathname]);
  return children;
}
