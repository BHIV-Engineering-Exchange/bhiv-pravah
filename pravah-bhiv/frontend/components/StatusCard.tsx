import { HealthBadge } from "@/components/HealthBadge";

type DomainStatus = {
  name: string;
  domain: string;
  url: string;
  status: string;
  health_score: number;
  response_time_ms: number;
  cpu_percent: number;
  memory_percent: number;
  uptime_percent: number;
  last_action: string;
  errors_24h: number;
};

type StatusCardProps = {
  item: DomainStatus;
};

export function StatusCard({ item }: StatusCardProps) {
  return (
    <article className="group rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 p-6 text-slate-200 shadow-xl transition-all duration-300 hover:bg-white/10 hover:-translate-y-1 hover:shadow-violet-500/10">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold tracking-tight text-white">{item.name}</h3>
          <p className="mt-1 text-sm text-slate-400">{item.domain}</p>
          <a href={item.url} target="_blank" rel="noreferrer" className="text-xs text-violet-400 hover:text-violet-300 transition-colors">
            {item.url}
          </a>
        </div>
        <HealthBadge status={item.status} />
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">Health Score</p>
          <p className="text-xl font-bold text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)] mt-1">{item.health_score}%</p>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">Response Time</p>
          <p className="text-xl font-bold text-sky-400 drop-shadow-[0_0_8px_rgba(56,189,248,0.3)] mt-1">{item.response_time_ms}ms</p>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">CPU / Memory</p>
          <p className="font-semibold text-slate-200 mt-1">{item.cpu_percent}% / {item.memory_percent}%</p>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">Uptime</p>
          <p className="font-semibold text-slate-200 mt-1">{item.uptime_percent}%</p>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">Last Action</p>
          <p className="font-semibold text-slate-200 mt-1 truncate" title={item.last_action}>{item.last_action}</p>
        </div>
        <div className="rounded-xl bg-white/5 border border-white/5 p-3 transition-colors group-hover:bg-white/10">
          <p className="text-slate-400 text-xs uppercase tracking-wider">Errors (24h)</p>
          <p className={`font-semibold mt-1 ${item.errors_24h > 0 ? "text-rose-400 drop-shadow-[0_0_8px_rgba(251,113,133,0.3)]" : "text-slate-200"}`}>{item.errors_24h}</p>
        </div>
      </div>
    </article>
  );
}
