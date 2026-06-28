import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { GraduationCap, Clock, ListChecks, ArrowLeft, ArrowRight, Brain, CheckCircle } from "@phosphor-icons/react";

const COLORS = {
  Beginner: "from-cyan-500/20 to-blue-500/10 border-cyan-400/30 text-cyan-300",
  Intermediate: "from-violet-500/20 to-fuchsia-500/10 border-violet-400/30 text-violet-300",
  Advanced: "from-amber-500/20 to-rose-500/10 border-amber-400/30 text-amber-300",
};

export default function AcademyDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setCourse(null); setNotFound(false);
    api.get(`/academy/${slug}`).then((r) => setCourse(r.data)).catch(() => setNotFound(true));
  }, [slug]);

  if (notFound) return (
    <section className="max-w-3xl mx-auto px-6 pt-32 pb-24 text-center">
      <h1 className="font-display font-bold text-3xl">Course not found</h1>
      <Link to="/academy" className="btn-primary mt-6 inline-flex">Back to Academy</Link>
    </section>
  );
  if (!course) return <section className="max-w-7xl mx-auto px-6 pt-32 pb-24 text-slate-400">Loading course…</section>;

  const askBrain = (q) => navigate(`/brain?q=${encodeURIComponent(q)}`);

  return (
    <>
      <SEO title={`${course.title} · LeadNation Academy`} description={course.summary} path={`/academy/${slug}`}
        keywords={`${course.title}, learn ${course.title}, trade course, ${course.level} export training`} />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-28 pb-8">
        <Link to="/academy" data-testid="academy-detail-back" className="text-xs text-slate-400 hover:text-cyan-300 flex items-center gap-1 mb-4"><ArrowLeft size={12} /> Back to Academy</Link>
        <div className="grid lg:grid-cols-2 gap-8 items-center">
          <div>
            <div className={`inline-block px-3 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase border bg-gradient-to-r ${COLORS[course.level] || COLORS.Beginner}`}>{course.level}</div>
            <h1 className="font-display font-extrabold text-4xl sm:text-5xl mt-4 leading-[1.05]">{course.title}</h1>
            <p className="mt-4 text-base text-slate-300">{course.summary}</p>
            <div className="mt-5 flex items-center gap-5 text-[11px] text-slate-400 font-mono-display tracking-widest uppercase">
              <span className="flex items-center gap-1"><Clock size={13} />{course.duration}</span>
              <span className="flex items-center gap-1"><ListChecks size={13} />{course.outline.length} lessons</span>
              <span className="flex items-center gap-1 text-emerald-300"><CheckCircle size={13} weight="fill" />100% free</span>
            </div>
            <button data-testid="academy-detail-ask-brain" onClick={() => askBrain(`Teach me about: ${course.title}`)}
              className="btn-primary mt-6 inline-flex"><Brain size={16} weight="duotone" /> Learn with the Brain</button>
          </div>
          <div className="relative h-64 lg:h-80 rounded-3xl overflow-hidden border border-white/10">
            <img src={course.image} alt={course.title} className="absolute inset-0 w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#050816]/70 to-transparent" />
          </div>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 sm:px-10 py-6">
        <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300 flex items-center gap-2 mb-4"><GraduationCap size={16} weight="duotone" /> Course curriculum</div>
        <div className="space-y-3">
          {course.outline.map((les) => (
            <div key={les.n} data-testid={`academy-lesson-${les.n}`} className="glass rounded-2xl p-5 flex gap-4 hover:border-cyan-400/30 transition-all">
              <div className="w-9 h-9 shrink-0 rounded-xl grid place-items-center bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 font-display font-bold">{les.n}</div>
              <div className="flex-1">
                <div className="font-display font-bold">{les.title}</div>
                <p className="text-sm text-slate-400 mt-1">{les.blurb}</p>
                <button onClick={() => askBrain(`Explain this trade lesson in detail: "${les.title}" (part of ${course.title})`)}
                  className="mt-3 text-xs text-cyan-300 hover:text-cyan-200 inline-flex items-center gap-1">
                  <Brain size={13} weight="duotone" /> Ask the Brain to teach this
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {course.related?.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 sm:px-10 py-8">
          <h2 className="font-display font-bold text-2xl mb-4">Continue learning</h2>
          <div className="grid md:grid-cols-3 gap-5">
            {course.related.map((c) => (
              <Link key={c.slug} to={`/academy/${c.slug}`} data-testid={`academy-related-${c.slug}`}
                className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group">
                <div className="h-36 relative overflow-hidden">
                  <img src={c.image} alt={c.title} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                </div>
                <div className="p-5">
                  <div className="font-display font-bold leading-tight">{c.title}</div>
                  <div className="mt-3 inline-flex items-center gap-2 text-cyan-300 text-sm">Start course <ArrowRight size={14} weight="bold" /></div>
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
