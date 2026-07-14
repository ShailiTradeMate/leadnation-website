import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import SEO, { eventSchema } from "@/components/SEO";
import DownloadCTA from "@/components/DownloadCTA";
import { fetchEventDetail, API } from "@/lib/api";
import {
  ArrowLeft, MapPin, CalendarBlank, Buildings, Users, Globe, Phone,
  EnvelopeSimple, CircleNotch, Package, Brain,
} from "@phosphor-icons/react";

const fmtDate = (s) => {
  if (!s) return "TBA";
  try { return new Date(s).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); }
  catch (_) { return s; }
};

export default function EventDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ev, setEv] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => { fetchEventDetail(id).then(setEv).catch(() => setEv(null)).finally(() => setReady(true)); }, [id]);

  if (ready && !ev) return (
    <section className="max-w-3xl mx-auto px-6 pt-32 pb-24 text-center">
      <h1 className="font-display font-bold text-3xl">Event not found</h1>
      <Link to="/expo" className="btn-primary mt-6 inline-flex">Back to Events</Link>
    </section>
  );
  if (!ev) return <section className="max-w-7xl mx-auto px-6 pt-32 pb-24 text-slate-400"><CircleNotch size={20} className="animate-spin inline" /> Loading event…</section>;

  const gallery = [...(ev.images || []), ...(ev.posters || []), ...(ev.flyers || [])].filter(Boolean);
  const media = (u) => (u?.startsWith("http") ? u : `${API.replace(/\/api$/, "")}${u}`);

  return (
    <>
      <SEO title={`${ev.name} · ${ev.city || ev.country} · LeadNation Events`} description={ev.description || ev.name} path={`/expo/${id}`}
        keywords={`${ev.category}, ${ev.country}, trade event, ${ev.name}`}
        image={ev.image ? media(ev.image) : undefined}
        schema={eventSchema({
          name: ev.name,
          description: ev.description || ev.name,
          startDate: ev.startDate,
          endDate: ev.endDate,
          location: [ev.venueName, ev.city, ev.country].filter(Boolean).join(", "),
          image: ev.image ? media(ev.image) : undefined,
          organizer: ev.organizer,
        })} />

      <section className="max-w-4xl mx-auto px-6 sm:px-10 pt-28 pb-8">
        <Link to="/expo" data-testid="event-detail-back" className="text-xs text-slate-400 hover:text-cyan-300 flex items-center gap-1 mb-4"><ArrowLeft size={12} /> Back to Events</Link>
        <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">{ev.category}</div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl mt-3 leading-[1.08]" data-testid="event-detail-name">{ev.name}</h1>

        <div className="relative h-72 sm:h-96 rounded-3xl overflow-hidden border border-white/10 mt-6">
          <img src={ev.image ? media(ev.image) : "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80"} alt={ev.name} className="absolute inset-0 w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#050816]/60 to-transparent" />
        </div>

        <div className="grid sm:grid-cols-2 gap-3 mt-6">
          <Info icon={CalendarBlank} label="Dates" value={`${fmtDate(ev.startDate)}${ev.endDate ? ` – ${fmtDate(ev.endDate)}` : ""}`} />
          <Info icon={MapPin} label="Location" value={[ev.venueName, ev.city, ev.country].filter(Boolean).join(", ")} />
          {ev.industry && <Info icon={Buildings} label="Industry" value={ev.industry} />}
          {ev.audience && <Info icon={Users} label="Audience" value={ev.audience} />}
          {ev.organizer && <Info icon={Buildings} label="Organizer" value={ev.organizer} />}
          {ev.products && <Info icon={Package} label="Products" value={ev.products} />}
        </div>

        {ev.description && <p className="mt-6 text-slate-200 leading-relaxed">{ev.description}</p>}

        {(ev.website || ev.contactEmail || ev.contactPhone) && (
          <div className="mt-6 flex flex-wrap gap-3">
            {ev.website && <a href={ev.website} target="_blank" rel="noopener noreferrer" className="btn-ghost !py-2 text-sm"><Globe size={14} weight="bold" /> Visit website</a>}
            {ev.contactEmail && <a href={`mailto:${ev.contactEmail}`} className="btn-ghost !py-2 text-sm"><EnvelopeSimple size={14} weight="bold" /> {ev.contactEmail}</a>}
            {ev.contactPhone && <a href={`tel:${ev.contactPhone}`} className="btn-ghost !py-2 text-sm"><Phone size={14} weight="bold" /> {ev.contactPhone}</a>}
          </div>
        )}

        {gallery.length > 0 && (
          <div className="mt-8">
            <h2 className="font-display font-bold text-xl mb-3">Posters & flyers</h2>
            <div className="grid sm:grid-cols-3 gap-3">
              {gallery.map((g, i) => (
                <a key={i} href={media(g)} target="_blank" rel="noopener noreferrer" className="block rounded-2xl overflow-hidden border border-white/10 aspect-[4/3]">
                  <img src={media(g)} alt="" className="w-full h-full object-cover hover:scale-105 transition-transform" />
                </a>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8 glass-strong rounded-2xl p-5 flex items-center gap-4 flex-wrap">
          <Brain size={28} weight="duotone" className="text-cyan-300" />
          <div className="flex-1 min-w-[220px]">
            <div className="font-display font-bold">Planning to attend or exhibit?</div>
            <div className="text-sm text-slate-400">Ask the LeadNation Brain how to prepare for {ev.name}.</div>
          </div>
          <button onClick={() => navigate(`/brain?q=${encodeURIComponent(`How should an exporter prepare for the trade event ${ev.name} in ${ev.country}?`)}`)} className="btn-primary">Ask the Brain</button>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-8 pb-12"><DownloadCTA /></section>
    </>
  );
}

const Info = ({ icon: Icon, label, value }) => (
  <div className="glass rounded-2xl px-4 py-3 flex items-start gap-3">
    <Icon size={18} weight="duotone" className="text-cyan-300 mt-0.5 shrink-0" />
    <div><div className="text-[10px] uppercase tracking-widest text-slate-400 font-mono-display">{label}</div><div className="text-sm text-slate-200">{value}</div></div>
  </div>
);
