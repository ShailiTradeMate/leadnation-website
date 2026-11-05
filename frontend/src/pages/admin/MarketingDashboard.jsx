import { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin";
import {
  FacebookLogo, InstagramLogo, LinkedinLogo, ArrowsClockwise, Megaphone, UsersThree, Eye, CursorClick,
  ChatCircleDots, Heart, ArrowSquareOut, WarningCircle, Target,
} from "@phosphor-icons/react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const RANGES = [["last_7d", "7 days"], ["last_30d", "30 days"], ["last_90d", "90 days"]];
const n = (v, d = 0) => (v == null ? "—" : Number(v).toLocaleString("en-IN", { maximumFractionDigits: d }));
const inr = (v) => `₹${n(v, 2)}`;
const day = (d) => (d ? new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "");

function Stat({ label, value, icon: I, tone = "text-cyan-300", testid }) {
  return (
    <div className="glass rounded-xl px-4 py-3" data-testid={testid}>
      <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-slate-400">
        <span>{label}</span>{I && <I size={14} weight="duotone" className={tone} />}
      </div>
      <div className="font-display font-bold text-xl mt-1" data-testid={testid ? `${testid}-value` : undefined}>{value}</div>
    </div>
  );
}

function Trend({ data, keys, colors, testid }) {
  const has = data?.some((p) => keys.some((k) => Number(p[k]) > 0));
  if (!has) return <div className="h-40 grid place-items-center text-xs text-slate-500" data-testid={`${testid}-empty`}>No activity recorded in this period yet.</div>;
  return (
    <div className="h-40" data-testid={testid}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            {keys.map((k, i) => (
              <linearGradient key={k} id={`g-${testid}-${k}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colors[i]} stopOpacity={0.5} /><stop offset="100%" stopColor={colors[i]} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey="date" tickFormatter={day} tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={24} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip labelFormatter={day} contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }} />
          {keys.map((k, i) => <Area key={k} type="monotone" dataKey={k} stroke={colors[i]} strokeWidth={2} fill={`url(#g-${testid}-${k})`} />)}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function Channel({ id, title, icon: I, accent, summary, children, posts, postCols, hasData, error }) {
  return (
    <section className="glass-strong rounded-2xl p-5 space-y-4" data-testid={`marketing-${id}`}>
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2"><I size={22} weight="duotone" style={{ color: accent }} /><h3 className="font-display font-bold text-lg">{title}</h3></div>
        {error ? <span className="text-xs text-amber-300 flex items-center gap-1" data-testid={`marketing-${id}-error`}><WarningCircle size={14} /> Windsor.ai did not answer for this source</span>
          : !hasData && <span className="text-xs text-slate-500" data-testid={`marketing-${id}-nodata`}>Connected · no data in this period yet</span>}
      </header>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">{summary}</div>
      {children}
      {posts?.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid={`marketing-${id}-posts`}>
            <thead><tr className="text-left text-[11px] uppercase tracking-widest text-slate-400">{postCols.map((c) => <th key={c.k} className="py-2 pr-3 font-medium">{c.l}</th>)}</tr></thead>
            <tbody>{posts.map((p) => (
              <tr key={p.id || p.date} className="border-t border-white/5">
                {postCols.map((c) => <td key={c.k} className="py-2 pr-3 text-slate-300 max-w-[320px] truncate">{c.r ? c.r(p) : n(p[c.k])}</td>)}
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function MarketingDashboard() {
  const [range, setRange] = useState("last_30d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = (refresh = false) => {
    setLoading(true); setErr("");
    adminApi.get(`/admin/marketing/overview?range=${range}${refresh ? "&refresh=true" : ""}`)
      .then((r) => setData(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Could not load marketing data"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [range]);

  const fb = data?.channels?.facebook, ig = data?.channels?.instagram, li = data?.channels?.linkedin, site = data?.site;
  const link = (p) => p.url ? <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-cyan-300 hover:underline inline-flex items-center gap-1">{p.caption || p.type || "post"} <ArrowSquareOut size={12} /></a> : (p.caption || p.type || "—");

  return (
    <div className="space-y-6" data-testid="admin-marketing">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2"><Megaphone size={14} weight="duotone" /> Marketing · Windsor.ai</div>
          <p className="text-sm text-slate-400 mt-1">Facebook Ads, Instagram and LinkedIn organic performance next to what the website converted. {data?.cached && <span className="text-slate-500">Cached · refreshed hourly.</span>}</p>
        </div>
        <div className="flex items-center gap-2">
          {RANGES.map(([k, l]) => (
            <button key={k} data-testid={`marketing-range-${k}`} onClick={() => setRange(k)}
              className={`px-3 py-1.5 rounded-full text-xs uppercase tracking-widest ${range === k ? "tab-active text-white" : "bg-white/5 text-slate-300"}`}>{l}</button>
          ))}
          <button data-testid="marketing-refresh" onClick={() => load(true)} disabled={loading} className="btn-ghost !py-1.5 !px-3 text-xs"><ArrowsClockwise size={14} className={loading ? "animate-spin" : ""} /> Refresh</button>
        </div>
      </div>

      {err && <div className="glass rounded-xl px-4 py-3 text-sm text-amber-200 flex items-center gap-2" data-testid="marketing-error"><WarningCircle size={16} /> {err}</div>}
      {data && !data.windsorConfigured && <div className="glass rounded-xl px-4 py-3 text-sm text-amber-200" data-testid="marketing-not-configured">Windsor.ai key is not configured on this server — only website conversions are shown.</div>}
      {loading && !data && <div className="glass rounded-xl p-8 text-center text-sm text-slate-400" data-testid="marketing-loading">Pulling the latest numbers from Windsor.ai…</div>}

      {site && (
        <section className="glass-strong rounded-2xl p-5" data-testid="marketing-site">
          <div className="flex items-center gap-2 mb-3"><Target size={20} weight="duotone" className="text-emerald-300" /><h3 className="font-display font-bold text-lg">Website conversions</h3><span className="text-xs text-slate-500">same triggers as the Meta Pixel, counted first-party</span></div>
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            <Stat label="Page views" value={n(site.pageViews)} icon={Eye} testid="site-pageviews" />
            <Stat label="Leads (all)" value={n(site.leads)} icon={Target} tone="text-emerald-300" testid="site-leads" />
            <Stat label="Contact form" value={n(site.contactLeads)} icon={ChatCircleDots} testid="site-contact" />
            <Stat label="Service requests" value={n(site.serviceLeads)} icon={ChatCircleDots} testid="site-service" />
            <Stat label="WhatsApp taps" value={n(site.whatsappLeads)} icon={CursorClick} tone="text-emerald-300" testid="site-whatsapp" />
            <Stat label="Registrations" value={n(site.registrations)} icon={UsersThree} tone="text-violet-300" testid="site-registrations" />
          </div>
        </section>
      )}

      {fb && (
        <Channel id="facebook" title="Facebook Ads" icon={FacebookLogo} accent="#1877F2" hasData={fb.hasData} error={data.errors?.facebook}
          summary={<>
            <Stat label="Spend" value={inr(fb.summary.spend)} testid="fb-spend" />
            <Stat label="Impressions" value={n(fb.summary.impressions)} icon={Eye} testid="fb-impressions" />
            <Stat label="Clicks · CTR" value={`${n(fb.summary.clicks)} · ${n(fb.summary.ctr, 2)}%`} icon={CursorClick} testid="fb-clicks" />
            <Stat label="Leads · Cost/lead" value={`${n(fb.summary.leads)} · ${fb.summary.leads ? inr(fb.summary.costPerLead) : "—"}`} icon={Target} tone="text-emerald-300" testid="fb-leads" />
          </>}
          posts={fb.campaigns?.filter((c) => c.spend > 0)} postCols={[{ k: "campaign", l: "Campaign", r: (p) => p.campaign }, { k: "spend", l: "Spend", r: (p) => inr(p.spend) }, { k: "impressions", l: "Impressions" }, { k: "clicks", l: "Clicks" }, { k: "leads", l: "Leads" }]}>
          <Trend data={fb.daily} keys={["impressions", "clicks"]} colors={["#1877F2", "#22d3ee"]} testid="fb-trend" />
          {!fb.hasData && <p className="text-xs text-slate-500">No campaigns have run yet — numbers appear here from the first paid campaign.</p>}
        </Channel>
      )}

      {ig && (
        <Channel id="instagram" title="Instagram · @vametra_ai" icon={InstagramLogo} accent="#E1306C" hasData={ig.hasData} error={data.errors?.instagram_account}
          summary={<>
            <Stat label="Followers" value={n(ig.summary.followers)} icon={UsersThree} tone="text-pink-300" testid="ig-followers" />
            <Stat label="Reach" value={n(ig.summary.reach)} icon={Eye} testid="ig-reach" />
            <Stat label="Profile views · Site clicks" value={`${n(ig.summary.profileViews)} · ${n(ig.summary.websiteClicks)}`} icon={CursorClick} testid="ig-profile" />
            <Stat label="Posts · Engagement" value={`${n(ig.summary.posts)} · ${n(ig.summary.engagement)}`} icon={Heart} tone="text-pink-300" testid="ig-posts" />
          </>}
          posts={ig.posts} postCols={[{ k: "date", l: "Date", r: (p) => day(p.date) }, { k: "caption", l: "Post", r: link }, { k: "reach", l: "Reach" }, { k: "likes", l: "Likes" }, { k: "comments", l: "Comments" }, { k: "saved", l: "Saves" }, { k: "engagement", l: "Engagement" }]}>
          <Trend data={ig.daily} keys={["reach_1d", "profile_views_1d"]} colors={["#E1306C", "#f59e0b"]} testid="ig-trend" />
        </Channel>
      )}

      {li && (
        <Channel id="linkedin" title="LinkedIn · Vametra AI" icon={LinkedinLogo} accent="#0A66C2" hasData={li.hasData} error={data.errors?.linkedin_account}
          summary={<>
            <Stat label="Followers" value={n(li.summary.followers)} icon={UsersThree} tone="text-sky-300" testid="li-followers" />
            <Stat label="Impressions" value={n(li.summary.impressions)} icon={Eye} testid="li-impressions" />
            <Stat label="Engagements · Rate" value={`${n(li.summary.engagements)} · ${n(li.summary.engagementRate, 2)}%`} icon={Heart} testid="li-engagements" />
            <Stat label="Clicks · Posts" value={`${n(li.summary.clicks)} · ${n(li.summary.posts)}`} icon={CursorClick} testid="li-clicks" />
          </>}
          posts={li.posts} postCols={[{ k: "date", l: "Date", r: (p) => day(p.date) }, { k: "text", l: "Post", r: (p) => p.text || "—" }, { k: "impressions", l: "Impressions" }, { k: "likes", l: "Likes" }, { k: "engagements", l: "Engagements" }, { k: "engagementRate", l: "Eng. rate %", r: (p) => n(p.engagementRate, 2) }]}>
          <Trend data={li.daily} keys={["impressions", "engagements"]} colors={["#0A66C2", "#22d3ee"]} testid="li-trend" />
        </Channel>
      )}

      {data?.generatedAt && <p className="text-[11px] text-slate-500" data-testid="marketing-generated">Data as of {new Date(data.generatedAt).toLocaleString("en-IN")} · Windsor.ai refreshes sources a few times a day; this view caches for 1 hour.</p>}
    </div>
  );
}
