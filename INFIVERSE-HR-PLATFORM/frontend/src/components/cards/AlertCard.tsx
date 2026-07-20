import type { ConstitutionalCardProps } from './types'
import { cardShellClassName } from './cardStyles'

export default function AlertCard({
  label,
  value,
  sublabel,
  readOnly = true,
  className = '',
}: ConstitutionalCardProps) {
  return (
    <div className={cardShellClassName('alert', className)} aria-readonly={readOnly} role="alert">
      <div className="flex items-center gap-2">
        <svg className="w-4 h-4 text-red-600 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <p className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wider">{label}</p>
      </div>
      <p className="text-xl font-bold text-red-600 dark:text-red-400">{value}</p>
      {sublabel && <p className="text-xs text-red-600/80 dark:text-red-400/80">{sublabel}</p>}
      <p className="text-[10px] text-slate-400 italic">Alert surface only — escalation authority remains with owning system</p>
    </div>
  )
}
