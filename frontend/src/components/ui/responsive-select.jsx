import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Command } from 'cmdk';
import { Check, ChevronDown, Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';

const text = children => React.Children.toArray(children).map(c =>
  typeof c === 'object' ? text(c.props?.children) : String(c)).join('');
const normalize = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
function optionsFrom(children, disabled = false) {
  return React.Children.toArray(children).flatMap(child => {
    if (!React.isValidElement(child)) return [];
    const p = child.props;
    if (child.type !== 'option') return optionsFrom(p.children, disabled || p.disabled);
    const label = text(p.children);
    return [{ value: String(p.value ?? label), label, display: p['data-display-label'] || label,
      search: p['data-search'] || '', disabled: disabled || p.disabled }];
  });
}

// A single touch/keyboard picker for existing native-select call sites. The event
// shape is preserved, so API payloads and parent form handlers do not change.
export const ResponsiveSelect = React.forwardRef(function ResponsiveSelect({
  children, value, defaultValue = '', onChange, className, placeholder = 'Select an option',
  allowCustom = false, loading = false, disabled, name, id, ...props
}, ref) {
  const uid = useId();
  const testid = props['data-testid'] || `select-${uid.replace(/:/g, '')}`;
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [localValue, setLocalValue] = useState(defaultValue);
  const contentRef = useRef(null);
  const current = String(value ?? localValue);
  const options = useMemo(() => optionsFrom(children), [children]);
  const selected = options.find(o => o.value === current);
  const matching = options.filter(o => normalize(`${o.label} ${o.value} ${o.search}`).includes(normalize(query)));
  const visible = options.length > 500 ? matching.slice(0, 200) : matching;
  const title = props['aria-label'] || placeholder;
  const choose = next => {
    setLocalValue(next);
    onChange?.({ target: { value: next, name }, currentTarget: { value: next, name } });
    setOpen(false);
  };
  useEffect(() => {
    if (!open) return;
    const viewport = window.visualViewport;
    const resize = () => {
      contentRef.current?.style.setProperty('--picker-height', `${Math.max(120, (viewport?.height || window.innerHeight) - 32)}px`);
      contentRef.current?.style.setProperty('--picker-top', `${(viewport?.offsetTop || 0) + 16}px`);
    };
    resize();
    viewport?.addEventListener('resize', resize);
    viewport?.addEventListener('scroll', resize);
    return () => { viewport?.removeEventListener('resize', resize); viewport?.removeEventListener('scroll', resize); };
  }, [open]);
  return (
    <Dialog.Root open={open} onOpenChange={next => { setOpen(next); if (next) setQuery(''); }}>
      {name && <input type="hidden" name={name} value={current} />}
      <Dialog.Trigger asChild>
        <button {...props} ref={ref} id={id} type="button" role="combobox" disabled={disabled}
          data-testid={testid} aria-expanded={open} aria-haspopup="dialog"
          aria-controls={open ? `${uid}-picker` : undefined}
          className={cn('responsive-select-trigger', className)}>
          <span className="min-w-0 flex-1 truncate text-left">{selected?.display || current || placeholder}</span>
          <ChevronDown aria-hidden="true" size={16} className="shrink-0 opacity-70" />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay data-testid={`${testid}-overlay`} className="location-picker-overlay" />
        <Dialog.Content ref={contentRef} id={`${uid}-picker`} data-testid={`${testid}-dialog`}
          className="location-picker-content" aria-describedby={undefined}
          onOpenAutoFocus={e => {
            // Opening a picker must not immediately cover the options with a phone keyboard.
            if (window.matchMedia('(pointer: coarse), (max-width: 639px)').matches) { e.preventDefault(); contentRef.current?.focus(); }
          }}>
          <div className="flex items-center justify-between gap-3 px-4 py-2 border-b border-white/10 shrink-0">
            <Dialog.Title className="text-base font-semibold truncate" data-testid={`${testid}-title`}>{title}</Dialog.Title>
            <Dialog.Close data-testid={`${testid}-close`} aria-label="Close options" className="p-3 rounded-lg hover:bg-white/10"><X size={18} /></Dialog.Close>
          </div>
          <Command shouldFilter={false} className="flex flex-col min-h-0 flex-1" loop>
            <div className="flex items-center gap-2 px-4 border-b border-white/10 shrink-0">
              <Search size={18} className="text-slate-400 shrink-0" />
              <Command.Input value={query} onValueChange={setQuery} data-testid={`${testid}-search`}
                placeholder="Search…" aria-label={`Search ${title.toLowerCase()}`} className="w-full min-w-0 bg-transparent outline-none py-3 text-base" />
            </div>
            <Command.List data-testid={`${testid}-options`} className="location-picker-list" aria-label={title}>
              {loading && <div data-testid={`${testid}-loading`} role="status" className="p-3 text-sm text-slate-400">Loading locations…</div>}
              {!loading && !matching.length && <div data-testid={`${testid}-empty`} role="status" className="p-3 text-sm text-slate-400">No matching options</div>}
              {visible.map((o, i) => <Command.Item key={o.value} value={`option-${i}`} disabled={o.disabled}
                data-testid={`${testid}-option-${encodeURIComponent(o.value) || 'empty'}`} data-value={o.value}
                onSelect={() => choose(o.value)} className="location-picker-option">
                <span className="min-w-0 flex-1 break-words">{o.label}</span>
                {o.value === current && <Check size={18} className="text-cyan-300 shrink-0" aria-hidden="true" />}
              </Command.Item>)}
              {matching.length > visible.length && <div data-testid={`${testid}-more`} className="p-3 text-xs text-slate-400">{matching.length} matches — refine your search to see more.</div>}
              {allowCustom && query.trim() && !options.some(o => normalize(o.label) === normalize(query.trim())) &&
                <Command.Item value="custom-location" data-testid={`${testid}-custom`} onSelect={() => choose(query.trim())} className="location-picker-option text-cyan-200">Use “{query.trim()}”</Command.Item>}
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
});