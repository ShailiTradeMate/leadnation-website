import React, { useEffect, useState } from "react";
import { PageHero } from "@/components/PageHero";
import DownloadCTA from "@/components/DownloadCTA";
import SEO from "@/components/SEO";
import { fetchCountries, fetchCustoms } from "@/lib/api";
import { Compass, CheckCircle, FileText, Truck, Clock, Lightbulb } from "@phosphor-icons/react";

export default function CustomsCompliance() {
  const [countries, setCountries] = useState([]);
  const [country, setCountry] = useState("IN");
  const [direction, setDirection] = useState("Import");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCountries().then(setCountries);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchCustoms(country, direction)
      .then(setData)
      .finally(() => setLoading(false));
  }, [country, direction]);

  return (
    <>
      <SEO
        title="Customs & Compliance Engine · 186+ Countries"
        description="Look up customs duty rates, document checklists and incoterms for any trade corridor. Live regulatory data for 186+ markets."
        path="/customs-compliance"
        keywords="customs duty by country, import documents required, export documentation, FTA benefits, DGFT, ICEGATE"
      />
      <PageHero
        testIdPrefix="customs"
        label="Customs & Compliance Engine"
        title="Decode every border. In seconds."
        sub="Select your country and trade direction. Get duty rates, document checklists, incoterms and pro tips — powered by the LeadNation compliance engine."
      />

      <section className="max-w-7xl mx-auto px-6 sm:px-10 grid lg:grid-cols-12 gap-8">
        {/* Selector */}
        <div className="lg:col-span-4">
          <div className="glass-strong rounded-3xl p-6 sticky top-24">
            <div className="text-xs font-mono-display tracking-[0.25em] uppercase text-cyan-300 mb-3">
              Configure
            </div>

            <label className="text-xs text-slate-400 block mb-2">Country</label>
            <select
              data-testid="customs-country-select"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full glass rounded-xl px-4 py-3 outline-none text-white"
            >
              {countries.map((c) => (
                <option key={c.code} value={c.code} className="bg-[#0a0f24]">
                  {c.flag} {c.name}
                </option>
              ))}
            </select>

            <label className="text-xs text-slate-400 block mt-5 mb-2">Direction</label>
            <div className="grid grid-cols-2 gap-2">
              {["Import", "Export"].map((d) => (
                <button
                  key={d}
                  data-testid={`customs-direction-${d.toLowerCase()}`}
                  onClick={() => setDirection(d)}
                  className={`py-2.5 rounded-xl text-sm font-medium transition-all ${
                    direction === d
                      ? "tab-active text-white"
                      : "bg-white/5 text-slate-300 hover:bg-white/10"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            <div className="mt-6 text-[11px] text-slate-500 leading-relaxed">
              Data shown is illustrative · production engine will sync live duty
              and document data from customs authorities and DGFT.
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-8 space-y-5">
          {loading || !data ? (
            <div className="glass rounded-3xl p-10 text-slate-400">Loading compliance brief…</div>
          ) : (
            <>
              <div className="glass-strong rounded-3xl p-7" data-testid="customs-result">
                <div className="flex items-center gap-3">
                  <Compass size={24} className="text-cyan-300" weight="duotone" />
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">
                    {data.direction} · {data.country}
                  </div>
                </div>
                <h2 className="font-display font-bold text-2xl sm:text-3xl mt-2">
                  {data.hsCodeExample}
                </h2>
                <div className="mt-6 grid sm:grid-cols-3 gap-4">
                  <Stat label="Duty Rate" value={data.dutyRate} />
                  <Stat label="Avg. Clearance" value={data.averageClearanceTime} />
                  <Stat label="Regulator" value={data.regulator} small />
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-5">
                <Card title="Required Documents" Icon={FileText}>
                  <ul className="space-y-2.5 mt-4">
                    {data.documents.map((d, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <CheckCircle size={16} weight="fill" className="text-cyan-300 mt-0.5 shrink-0" />
                        {d}
                      </li>
                    ))}
                  </ul>
                </Card>
                <Card title="Incoterms" Icon={Truck}>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {data.incoterms.map((i) => (
                      <span key={i} className="px-3 py-1.5 rounded-full text-xs font-mono-display tracking-widest bg-white/5 border border-white/10">
                        {i}
                      </span>
                    ))}
                  </div>
                  <div className="mt-6 text-sm text-slate-400">
                    <Clock size={14} className="inline mr-2 text-cyan-300" />
                    {data.restrictions}
                  </div>
                </Card>
              </div>

              <div className="glass rounded-3xl p-6 flex items-start gap-4 border border-cyan-500/20">
                <Lightbulb size={26} weight="duotone" className="text-cyan-300 shrink-0" />
                <div>
                  <div className="text-xs font-mono-display tracking-[0.3em] uppercase text-cyan-300">Pro tip</div>
                  <div className="mt-1 text-slate-200">{data.tip}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 sm:px-10 pt-20 pb-12">
        <DownloadCTA />
      </section>
    </>
  );
}

function Stat({ label, value, small = false }) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="text-[10px] uppercase tracking-[0.25em] text-slate-400 font-mono-display">{label}</div>
      <div className={`mt-2 font-display font-bold ${small ? "text-sm" : "text-xl"}`}>{value}</div>
    </div>
  );
}
function Card({ title, Icon, children }) {
  return (
    <div className="glass rounded-3xl p-6">
      <div className="flex items-center gap-2">
        <Icon size={20} className="text-cyan-300" weight="duotone" />
        <div className="font-display font-bold">{title}</div>
      </div>
      {children}
    </div>
  );
}
