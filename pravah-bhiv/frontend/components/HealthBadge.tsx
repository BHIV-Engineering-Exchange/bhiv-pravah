type HealthBadgeProps = {
  status: string;
};

const toneClass: Record<string, string> = {
  CONNECTED: "bg-emerald-500/20 text-emerald-200 border-emerald-400/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]",
  HEALTHY: "bg-emerald-500/20 text-emerald-200 border-emerald-400/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]",
  DISCONNECTED: "bg-rose-500/20 text-rose-200 border-rose-400/40 shadow-[0_0_10px_rgba(244,63,94,0.3)]",
  DOWN: "bg-rose-500/20 text-rose-200 border-rose-400/40 shadow-[0_0_10px_rgba(244,63,94,0.3)]",
  DEGRADED: "bg-amber-500/20 text-amber-200 border-amber-400/40 shadow-[0_0_10px_rgba(245,158,11,0.3)]",
  MEDIUM: "bg-amber-500/20 text-amber-200 border-amber-400/40 shadow-[0_0_10px_rgba(245,158,11,0.3)]",
  CRITICAL: "bg-rose-500/20 text-rose-200 border-rose-400/40 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
};

export function HealthBadge({ status }: HealthBadgeProps) {
  const normalized = status.toUpperCase();
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-bold tracking-wider backdrop-blur-md ${toneClass[normalized] ?? "bg-slate-800/50 text-slate-200 border-slate-600/50"}`}
    >
      {status}
    </span>
  );
}
