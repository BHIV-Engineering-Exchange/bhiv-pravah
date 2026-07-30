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

function CircularProgress({ percentage, colorClass }: { percentage: number, colorClass: string }) {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  return (
    <div className="relative flex items-center justify-center w-16 h-16">
      <svg className="absolute inset-0 w-full h-full transform -rotate-90">
        <circle
          cx="32" cy="32" r="22"
          stroke="currentColor" strokeWidth="3" fill="transparent"
          className="text-slate-800"
        />
        <circle
          cx="32" cy="32" r="22"
          stroke="currentColor" strokeWidth="3" fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className={`${colorClass} transition-all duration-1000 ease-out`}
        />
      </svg>
      <span className={`text-sm font-bold ${colorClass}`}>{percentage}</span>
    </div>
  );
}

export function StatusCard({ item }: StatusCardProps) {
  const isHealthy = item.health_score > 80;
  const isWarning = item.health_score > 50 && item.health_score <= 80;
  
  const healthColor = isHealthy ? "text-teal-400" : isWarning ? "text-amber-400" : "text-rose-400";
  const bgGlow = isHealthy ? "shadow-[0_0_30px_rgba(20,184,166,0.1)]" : isWarning ? "shadow-[0_0_30px_rgba(251,191,36,0.1)]" : "shadow-[0_0_30px_rgba(244,63,94,0.1)]";
  
  return (
    <article className={`glass-card p-6 text-slate-200 group flex flex-col justify-between ${bgGlow} transition-all duration-300 hover:-translate-y-1`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-display font-bold tracking-tight text-white">{item.name}</h3>
            {(item.status === "CONNECTED" || item.status === "HEALTHY") && (
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal-500"></span>
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-400 font-medium">{item.domain}</p>
          <a href={item.url} target="_blank" rel="noreferrer" className="text-xs text-sky-400 hover:text-sky-300 transition-colors hover:underline mt-1.5 inline-block opacity-80 hover:opacity-100">
            {item.url}
          </a>
        </div>
        <div className="flex flex-col items-end gap-3">
          <HealthBadge status={item.status} />
          <CircularProgress percentage={item.health_score} colorClass={healthColor} />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-4 transition-colors group-hover:border-slate-600/50">
          <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">Response Time</p>
          <p className="text-2xl font-display font-bold text-sky-400 mt-1">{item.response_time_ms}<span className="text-sm font-medium text-sky-500/70 ml-1">ms</span></p>
        </div>
        <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-4 transition-colors group-hover:border-slate-600/50">
          <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">CPU / Memory</p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="font-semibold text-slate-200 text-lg">{item.cpu_percent}%</span>
            <span className="text-slate-700">|</span>
            <span className="font-semibold text-slate-200 text-lg">{item.memory_percent}%</span>
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-4 transition-colors group-hover:border-slate-600/50 flex flex-col justify-center">
          <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">Uptime</p>
          <p className="font-semibold text-slate-200 mt-1 text-lg">{item.uptime_percent}%</p>
        </div>
        <div className="rounded-lg bg-slate-900/50 border border-slate-700/50 p-4 transition-colors group-hover:border-slate-600/50 flex flex-col justify-center">
          <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">Errors (24h)</p>
          <p className={`font-semibold mt-1 text-lg ${item.errors_24h > 0 ? "text-rose-400 text-glow-sm" : "text-teal-400"}`}>{item.errors_24h}</p>
        </div>
      </div>
      <div className="mt-3 rounded-lg bg-slate-900/50 border border-slate-700/50 p-3 transition-colors group-hover:border-slate-600/50 flex items-center justify-between">
        <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">Last Action</span>
        <span className="font-semibold text-slate-300 text-xs truncate max-w-[200px]" title={item.last_action}>{item.last_action}</span>
      </div>
    </article>
  );
}
