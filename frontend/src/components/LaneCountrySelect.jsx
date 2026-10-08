import React, { useEffect, useState } from "react";
import { ResponsiveSelect } from "@/components/ui/responsive-select";
import { api } from "@/lib/api";

let _cache = null;
export const fetchLaneCountries = () => {
  if (_cache) return Promise.resolve(_cache);
  return api.get("/duty/countries").then((r) => { _cache = r.data.countries || []; return _cache; }).catch(() => []);
};

/** Country picker restricted to the 56 markets with live WITS tariff coverage (ISO-numeric values the duty
 *  and Command Center engines expect). Replaces the generic 250-country list that silently returned no data. */
export const LaneCountrySelect = ({ value, onChange, testId, className, allowAny = false, anyLabel = "— Any —" }) => {
  const [rows, setRows] = useState(_cache || []);
  useEffect(() => { if (!_cache) fetchLaneCountries().then(setRows); }, []);
  return (
    <ResponsiveSelect data-testid={testId} className={className} value={value} onChange={onChange}>
      {allowAny && <option value="">{anyLabel}</option>}
      {rows.map((c) => <option key={c.code} value={c.code}>{c.flag ? `${c.flag} ` : ""}{c.name}</option>)}
    </ResponsiveSelect>
  );
};
