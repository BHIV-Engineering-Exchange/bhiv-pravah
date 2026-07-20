import type { ConstitutionalCardProps } from './types'
import { cardShellClassName } from './cardStyles'

export default function GovernanceCard({
  label,
  value,
  sublabel,
  severity = 'normal',
  readOnly = true,
  className = '',
}: ConstitutionalCardProps) {
  return (
    <div className={cardShellClassName(severity, className)} aria-readonly={readOnly}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</p>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 dark:bg-slate-700/50 dark:text-slate-200">Governance</span>
      </div>
      <p className="text-xl font-bold text-slate-900 dark:text-white">{value}</p>
      {sublabel && <p className="text-xs text-slate-500 dark:text-slate-400">{sublabel}</p>}
      <p className="text-[10px] text-slate-400 italic">Dashboard ≠ Governance — visibility only</p>
    </div>
  )
}
