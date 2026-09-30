import React, { useEffect, useMemo, useState } from 'react';
import { ResponsiveSelect } from '@/components/ui/responsive-select';
import { COUNTRY_OPTIONS, loadLocalities } from '@/data/geo';

export const CountrySelect = ({ value, onChange, valueType = 'name', placeholder = 'Select country', ...props }) => (
  <ResponsiveSelect {...props} value={value} onChange={onChange} placeholder={placeholder} aria-label={props['aria-label'] || 'Country'}>
    <option value="">{placeholder}</option>
    {COUNTRY_OPTIONS.map(c => <option key={c.code} value={valueType === 'code' ? c.code : c.name} data-search={c.code}>{c.name}</option>)}
  </ResponsiveSelect>
);

export const LocalitySelect = ({ country, state, kind, value, onChange, ...props }) => {
  const [data, setData] = useState({ states: [], cities: [] });
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    setData({ states: [], cities: [] }); setFailed(false); setLoading(Boolean(country));
    loadLocalities(country).then(d => { if (active) setData(d); })
      .catch(() => { if (active) setFailed(true); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [country]);
  const names = useMemo(() => {
    if (kind === 'state') return data.states.map(s => s.name).sort((a, b) => a.localeCompare(b));
    const code = data.states.find(s => s.name === state || s.code === state)?.code;
    return [...new Set(data.cities.filter(c => !code || c[1] === code).map(c => c[0]))].sort((a, b) => a.localeCompare(b));
  }, [data, kind, state]);
  const label = kind === 'state' ? 'State / Province' : 'City';
  return <>
    <ResponsiveSelect {...props} value={value || ''} onChange={onChange} disabled={!country}
      aria-label={label} placeholder={country ? `Select ${label.toLowerCase()}` : 'Select a country first'} allowCustom loading={loading}>
      <option value="">{`Select ${label.toLowerCase()}`}</option>
      {names.map(n => <option key={n} value={n}>{n}</option>)}
    </ResponsiveSelect>
    {failed && <span role="status" data-testid={`${props['data-testid']}-load-error`} className="block text-xs text-amber-200 mt-1">Location list unavailable. You can still enter your locality in search.</span>}
  </>;
};