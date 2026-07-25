type MetricCardProps = {
  label: string;
  value: string | number;
  tone?: "default" | "green" | "orange" | "blue" | "red";
  className?: string;
};

const toneClass: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-slate-100",
  green: "text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.3)]",
  orange: "text-amber-400 drop-shadow-[0_0_10px_rgba(251,191,36,0.3)]",
  blue: "text-sky-400 drop-shadow-[0_0_10px_rgba(56,189,248,0.3)]",
  red: "text-rose-400 drop-shadow-[0_0_10px_rgba(251,113,133,0.3)]"
};

export function MetricCard({ label, value, tone = "default", className = "" }: MetricCardProps) {
  return (
    <article className={`group rounded-2xl bg-white/5 backdrop-blur-md border border-white/5 p-5 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-white/10 hover:shadow-violet-500/10 ${className}`}>
      <p className={`text-3xl font-bold tracking-tight transition-colors ${toneClass[tone]}`}>{value}</p>
      <p className="mt-2 text-sm font-medium text-slate-400 transition-colors group-hover:text-slate-300">{label}</p>
    </article>
  );
}
