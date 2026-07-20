import type { ConstitutionalCardProps } from './types'
import { cardShellClassName } from './cardStyles'

export default function ReplayCard({
  label,
  value,
  sublabel,
  correlationId,
  readOnly = true,
  className = '',
}: ConstitutionalCardProps) {
  return (
    <div className={cardShellClassName('normal', className)} aria-readonly={readOnly}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{label}</p>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">Replay</span>
      </div>
      <p className="text-xl font-bold text-slate-900 dark:text-white">{value}</p>
      {sublabel && <p className="text-xs text-slate-500 dark:text-slate-400">{sublabel}</p>}
      {correlationId && <p className="text-[10px] font-mono text-slate-400 truncate">cid: {correlationId}</p>}
      <p className="text-[10px] text-slate-400 italic">Read-only reconstruction — no execution replay</p>
    </div>
  )
}
