import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import DownloadCTA from "@/components/DownloadCTA";
import SEO, { articleSchema } from "@/components/SEO";
import { fetchNewsDetail, fetchNewsFeed } from "@/lib/api";
import { Clock, ArrowLeft, Brain, ArrowUpRight, ArrowSquareOut, CircleNotch } from "@phosphor-icons/react";

function Impact({ text }) {
  const lines = (text || "").split("\n").filter((l) => l.trim());
  return (
    <div className="space-y-1.5 text-sm text-slate-200">
      {lines.map((l, i) => {
        const t = l.replace(/^[-*]\s?/, "").trim();
        const isBullet = /^[-*]\s/.test(l);
        return isBullet
          ? <div key={i} className="flex gap-2"><span className="text-cyan-300">•</span><span>{t}</span></div>
          : <p key={i}>{t}</p>;
      })}
    </div>
  );
}

export default function TradeNewsDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [others, setOthers] = useState([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(false);
    fetchNewsDetail(id).then(setItem).catch(() => setItem(null)).finally(() => setReady(true));
    fetchNewsFeed({ limit: 4 }).then((d) => setOthers((d.items || []).filter((n) => String(n.id) !== String(id)).slice(0, 3))).catch(() => {});
  }, [id]);

  if (ready && !item) return (
    <section className="max-w-3xl mx-auto px-6 pt-32 pb-24 text-center">
      <h1 className="font-display font-bold text-3xl">Story not found</h1>
      <Link to="/trade-news" className="btn-primary mt-6 inline-flex">Back to Trade News</Link>
    </section>
  );
  if (!item) return <section className="max-w-7xl mx-auto px-6 pt-32 pb-24 text-slate-400"><CircleNotch size={20} className="animate-spin inline" /> Loading story…</section>;

  return (
    <>
      <SEO title={`${item.title} · LeadNation Trade News`} description={item.excerpt} path={`/trade-news/${id}`}
        keywords={`${item.category}, trade news, ${item.title}`}
        type="article"
        image={item.image || item.image_url || undefined}
        schema={articleSchema({
          type: "NewsArticle",
          headline: item.title,
          description: item.excerpt,
          path: `/trade-news/${id}`,
          section: item.category,
          image: item.image || item.image_url,
          datePublished: item.published_at || item.date || item.created_at,
          keywords: `${item.category}, global trade news`,
        })} />

      <section className="max-w-4xl mx-auto px-6 sm:px-10 pt-28 pb-8">
        <Link to="/trade-news" data-testid="news-detail-back" className="text-xs text-slate-400 hover:text-cyan-300 flex items-center gap-1 mb-4"><ArrowLeft size={12} /> Back to Trade News</Link>
        <div className="text-[11px] font-mono-display tracking-[0.3em] uppercase text-cyan-300">{item.category}</div>
        <h1 className="font-display font-extrabold text-3xl sm:text-5xl mt-3 leading-[1.08]">{item.title}</h1>
        <div className="mt-4 flex items-center gap-4 text-xs text-slate-400 font-mono-display tracking-widest uppercase">
          <span className="flex items-center gap-1"><Clock size={12} />{item.date}</span><span>·</span><span>{item.source}</span>
          {item.country && item.country !== "Global" && <><span>·</span><span>{item.country}</span></>}
        </div>
        <div className="relative h-72 sm:h-96 rounded-3xl overflow-hidden border border-white/10 mt-6">
          <img src={item.image} alt="" className="absolute inset-0 w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#050816]/60 to-transparent" />
        </div>
        <p className="mt-6 text-lg text-slate-200 leading-relaxed">{item.excerpt}</p>
        {item.body && item.body !== item.excerpt && <p className="mt-4 text-slate-300 leading-relaxed whitespace-pre-line">{item.body.slice(0, 1200)}</p>}
        {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex items-center gap-1 text-sm text-cyan-300 hover:underline">Read full source <ArrowSquareOut size={13} /></a>}

        {/* Brain impact */}
        <div className="mt-8 glass-strong rounded-2xl p-6" data-testid="news-detail-impact">
          <div className="flex items-center gap-2 mb-3">
            <Brain size={22} weight="duotone" className="text-cyan-300" />
            <div className="font-display font-bold text-lg">What does this mean for your trade?</div>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-400/20">LeadNation Brain</span>
          </div>
          <Impact text={item.impact} />
          <button data-testid="news-detail-ask-brain"
            onClick={() => navigate(`/brain?q=${encodeURIComponent(`What does this trade news mean for my business: ${item.title}`)}`)}
            className="btn-ghost !py-2 text-sm mt-4">Ask a follow-up →</button>
        </div>
      </section>

      {others.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 py-8">
          <h2 className="font-display font-bold text-2xl mb-4">More headlines</h2>
          <div className="grid md:grid-cols-3 gap-5">
            {others.map((n) => (
              <Link key={n.id} to={`/trade-news/${n.id}`} className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group">
                <div className="h-36 relative overflow-hidden">
                  <img src={n.image} alt="" className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                </div>
                <div className="p-5">
                  <div className="font-display font-bold leading-tight line-clamp-2">{n.title}</div>
                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 font-mono-display uppercase">
                    <span>{n.date}</span><ArrowUpRight size={14} className="text-cyan-300" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-12 pb-12"><DownloadCTA /></section>
    </>
  );
}
