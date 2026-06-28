import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const DEFAULTS = {
  accentColor: "#00C2FF",
  maintenance: false,
  maintenanceMessage: "We're making improvements — back shortly.",
  features: {
    customs: true, academy: true, intelligence: true, blog: true,
    trade_news: true, tools: true, services: true, brain: true, expo: true,
  },
  serviceRates: {},
};

const SettingsContext = createContext({ settings: DEFAULTS, loaded: false, refresh: () => {} });

export function useSettings() {
  return useContext(SettingsContext);
}

function applyAccent(color) {
  if (color) document.documentElement.style.setProperty("--ln-secondary", color);
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(DEFAULTS);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/settings");
      const merged = { ...DEFAULTS, ...data, features: { ...DEFAULTS.features, ...(data.features || {}) } };
      setSettings(merged);
      applyAccent(merged.accentColor);
    } catch (_) {
      /* keep defaults */
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <SettingsContext.Provider value={{ settings, loaded, refresh }}>
      {children}
    </SettingsContext.Provider>
  );
}
