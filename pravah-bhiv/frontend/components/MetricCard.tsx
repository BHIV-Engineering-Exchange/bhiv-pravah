type MetricCardProps = {
  label: string;
  value: string | number;
  tone?: "default" | "green" | "orange" | "blue" | "red";
  className?: string;
};

const toneTextClass: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-slate-100",
  green: "text-teal-400 text-glow-sm",
  orange: "text-amber-400 text-glow-sm",
  blue: "text-sky-400 text-glow-sm",
  red: "text-rose-400 text-glow-sm"
};

const toneLineBg: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "bg-slate-700",
  green: "bg-teal-500",
  orange: "bg-amber-500",
  blue: "bg-sky-500",
  red: "bg-rose-500"
};

export function MetricCard({ label, value, tone = "default", className = "" }: MetricCardProps) {
  return (
    <article className={`glass-card p-5 group ${className} flex flex-col justify-between h-full`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest transition-colors group-hover:text-slate-300">
          {label}
        </p>
        <div className={`w-2 h-2 rounded-full ${toneLineBg[tone]} shadow-glow-${tone === 'green' ? 'success' : tone === 'red' ? 'danger' : 'primary'} opacity-80 group-hover:opacity-100 transition-opacity`} />
      </div>
      <div>
        <p className={`text-3xl font-display font-bold tracking-tight transition-all duration-300 ${toneTextClass[tone]}`}>
          {value}
        </p>
      </div>
    </article>
  );
}
