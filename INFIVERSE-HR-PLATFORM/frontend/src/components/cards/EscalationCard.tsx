import type { ConstitutionalCardProps } from './types'
import { cardShellClassName } from './cardStyles'

export default function EscalationCard({
  label,
  value,
  sublabel,
  severity = 'warning',
  readOnly = true,
  className = '',
}: ConstitutionalCardProps) {
  return (
    <div className={cardShellClassName(severity, className)} aria-readonly={readOnly}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</p>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">Escalation</span>
      </div>
      <p className="text-xl font-bold text-slate-900 dark:text-white">{value}</p>
      {sublabel && <p className="text-xs text-slate-500 dark:text-slate-400">{sublabel}</p>}
      <p className="text-[10px] text-slate-400 italic">Pending review visibility — human governance required to act</p>
    </div>
  )
}
