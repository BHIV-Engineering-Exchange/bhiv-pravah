import type { ConstitutionalCardProps } from './types'
import { cardShellClassName } from './cardStyles'

export default function TelemetryCard({
  label,
  value,
  sublabel,
  severity = 'normal',
  sourceSystem,
  readOnly = true,
  className = '',
}: ConstitutionalCardProps) {
  return (
    <div className={cardShellClassName(severity, className)} aria-readonly={readOnly}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</p>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">Telemetry</span>
      </div>
      <p className="text-xl font-bold text-slate-900 dark:text-white">{value}</p>
      {sublabel && <p className="text-xs text-slate-500 dark:text-slate-400">{sublabel}</p>}
      {sourceSystem && <p className="text-[10px] text-slate-400">Endpoint: {sourceSystem}</p>}
      <p className="text-[10px] text-slate-400 italic">Replay ≠ Execution — telemetry visibility only</p>
    </div>
  )
}
