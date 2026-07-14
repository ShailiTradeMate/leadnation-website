import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO, { articleSchema } from "@/components/SEO";
import { api } from "@/lib/api";
import { Clock, ArrowRight } from "@phosphor-icons/react";

export function BlogIndex() {
  const [posts, setPosts] = useState([]);
  useEffect(() => { api.get("/blog").then((r) => setPosts(r.data)); }, []);

  return (
    <>
      <SEO title="LeadNation Blog · Export, Import, Compliance & Trade News"
        description="Long-form guides for global traders — export, import, compliance, logistics and trade intelligence. Updated weekly."
        path="/blog"
        keywords="trade blog India, export blog, import blog, RoDTEP guide, customs blog, trade compliance guide"
      />
      <PageHero testIdPrefix="blog" label="Knowledge Center"
        title="Stories, guides & playbooks for traders."
        sub="The long-form library that turns first-time exporters into seasoned operators."
      />
      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {posts.map((p, i) => (
            <Link key={p.slug} to={`/blog/${p.slug}`} data-testid={`blog-card-${i}`}
              className="group glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all">
              <div className="h-44 relative overflow-hidden">
                <img src={p.image} alt={p.title} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                <div className="absolute top-3 left-3 glass px-2 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase text-cyan-300">{p.category}</div>
              </div>
              <div className="p-5">
                <h3 className="font-display font-bold text-lg leading-tight">{p.title}</h3>
                <p className="mt-2 text-sm text-slate-400 line-clamp-2">{p.excerpt}</p>
                <div className="mt-3 text-[11px] font-mono-display tracking-widest uppercase text-slate-400 flex items-center gap-3">
                  <span>{p.date}</span><span className="flex items-center gap-1"><Clock size={10} />{p.readMins} min</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-12"><DownloadCTA /></section>
    </>
  );
}

export default function BlogDetail() {
  const { slug } = useParams();
  const [p, setP] = useState(null);
  const [nf, setNf] = useState(false);
  useEffect(() => { setP(null); setNf(false); api.get(`/blog/${slug}`).then((r) => r.data?.error ? setNf(true) : setP(r.data)).catch(() => setNf(true)); }, [slug]);

  if (nf) return <div className="max-w-7xl mx-auto px-6 py-32 text-center"><h1 className="font-display font-extrabold text-4xl">Post not found</h1><Link to="/blog" className="btn-primary mt-6 inline-flex">Back to blog</Link></div>;
  if (!p) return <div className="max-w-7xl mx-auto px-6 py-32 text-slate-400">Loading…</div>;

  return (
    <>
      <SEO title={p.title} description={p.excerpt} path={`/blog/${p.slug}`} type="article"
        keywords={`${p.category}, ${p.title}, trade blog`}
        schema={articleSchema({ type: "BlogPosting", headline: p.title, description: p.excerpt, path: `/blog/${p.slug}`, datePublished: p.date, image: p.image, section: p.category, keywords: `${p.category}, trade blog` })}
      />
      <article className="max-w-3xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">{p.category} · {p.date} · {p.readMins} min read</div>
        <h1 data-testid="blog-title" className="font-display font-extrabold tracking-tight text-4xl sm:text-5xl mt-4 leading-[1.1]">{p.title}</h1>
        <p className="mt-5 text-slate-300 text-lg">{p.excerpt}</p>
        <div className="mt-8 rounded-3xl overflow-hidden h-72 relative">
          <img src={p.image} alt={p.title} className="absolute inset-0 w-full h-full object-cover" />
        </div>
        <div className="mt-10 space-y-5 text-slate-200 text-base leading-relaxed">
          {p.body.map((para, i) => <p key={i}>{para}</p>)}
        </div>
        <div className="mt-10 glass-strong rounded-3xl p-7 flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <div className="font-display font-bold text-xl">Ready to put this into action?</div>
            <div className="text-sm text-slate-400">Open the LeadNation app to run the checklist on your next shipment.</div>
          </div>
          <Link to="/contact" className="btn-primary">Create free account <ArrowRight size={14} weight="bold" /></Link>
        </div>
      </article>
      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-8 pb-12"><DownloadCTA /></section>
    </>
  );
}
