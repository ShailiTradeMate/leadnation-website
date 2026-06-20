import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { api } from "@/lib/api";
import { GraduationCap, Clock, ListChecks, ArrowRight } from "@phosphor-icons/react";

const LEVELS = ["Beginner", "Intermediate", "Advanced"];
const COLORS = {
  Beginner: "from-cyan-500/20 to-blue-500/10 border-cyan-400/30 text-cyan-300",
  Intermediate: "from-violet-500/20 to-fuchsia-500/10 border-violet-400/30 text-violet-300",
  Advanced: "from-amber-500/20 to-rose-500/10 border-amber-400/30 text-amber-300",
};

export default function Academy() {
  const [data, setData] = useState({});
  const [level, setLevel] = useState("Beginner");

  useEffect(() => {
    api.get("/academy").then((r) => setData(r.data || {}));
  }, []);

  return (
    <>
      <SEO
        title="Trade Learning Academy · Free Import, Export & Customs Courses"
        description="Master international trade in 6 weeks. Free, structured lessons on import process, export process, documentation, customs clearance, FTA arbitrage and more."
        path="/academy"
        keywords="learn international trade, import process course, export process course, customs clearance training, trade documentation tutorial, FTA learning"
        schema={{
          "@context": "https://schema.org",
          "@type": "EducationalOrganization",
          name: "LeadNation Academy",
          url: "https://leadnation.app/academy",
        }}
      />

      <PageHero
        testIdPrefix="academy"
        label="LeadNation Academy"
        title="Master global trade. In weeks, not years."
        sub="From your very first export inquiry to FTA arbitrage — premium lessons by traders, for traders. 100% free."
      >
        <div className="flex gap-2 flex-wrap">
          {LEVELS.map((l) => (
            <button
              key={l}
              data-testid={`academy-tab-${l.toLowerCase()}`}
              onClick={() => setLevel(l)}
              className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all ${
                level === l ? "tab-active text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </PageHero>

      <section className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {(data[level] || []).map((c, i) => (
            <article
              key={c.slug}
              data-testid={`academy-course-${i}`}
              className="glass rounded-3xl overflow-hidden hover:border-cyan-400/30 hover:-translate-y-1 transition-all group cursor-pointer"
            >
              <div className="relative h-44 overflow-hidden">
                <img src={c.image} alt={c.title} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-[2s]" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f24] via-transparent to-transparent" />
                <div className={`absolute top-3 left-3 px-3 py-1 rounded-full text-[10px] font-mono-display tracking-widest uppercase border bg-gradient-to-r ${COLORS[level]}`}>
                  {level}
                </div>
              </div>
              <div className="p-6">
                <h3 className="font-display font-bold text-lg leading-tight">{c.title}</h3>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">{c.summary}</p>
                <div className="mt-4 flex items-center gap-4 text-[11px] text-slate-400 font-mono-display tracking-widest uppercase">
                  <span className="flex items-center gap-1"><Clock size={12} />{c.duration}</span>
                  <span className="flex items-center gap-1"><ListChecks size={12} />{c.lessons} lessons</span>
                </div>
                <div className="mt-5 inline-flex items-center gap-2 text-cyan-300 text-sm font-medium">
                  Start lesson <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="mt-16 glass-strong rounded-3xl p-8 sm:p-10 flex items-center gap-5 flex-wrap">
          <GraduationCap size={42} weight="duotone" className="text-cyan-300" />
          <div className="flex-1 min-w-[260px]">
            <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">For Indian exporters</div>
            <div className="font-display font-bold text-xl mt-1">Unlock RoDTEP, DGFT and MSME modules inside the app.</div>
          </div>
          <a href="#download" className="btn-primary">Download app</a>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA id="download" />
      </section>
    </>
  );
}
