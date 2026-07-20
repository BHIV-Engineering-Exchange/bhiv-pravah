import type { ConstitutionalCardProps } from './types'
import { OBSERVABILITY_DISCLAIMER, cardShellClassName, severityClasses } from './cardStyles'

export default function ExecutiveMetricCard({
  label,
  value,
  sublabel,
  delta,
  deltaPositive,
  severity = 'normal',
  sourceSystem,
  correlationId,
  readOnly = true,
  disclaimer = OBSERVABILITY_DISCLAIMER,
  className = '',
}: ConstitutionalCardProps) {
  const { valueColor } = severityClasses(severity)

  return (
    <div className={cardShellClassName(severity, className)} aria-readonly={readOnly}>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate">{label}</p>
      <p className={`text-2xl font-bold font-heading ${valueColor}`}>{value}</p>
      {sublabel && <p className="text-xs text-slate-500 dark:text-slate-400 leading-tight">{sublabel}</p>}
      {delta && (
        <p className={`text-xs font-semibold ${deltaPositive ? 'text-emerald-600' : 'text-red-600'}`}>{delta}</p>
      )}
      {sourceSystem && (
        <p className="text-[10px] text-slate-400 dark:text-slate-500">Source: {sourceSystem}{correlationId ? ` · ${correlationId.slice(0, 8)}…` : ''}</p>
      )}
      <p className="text-[10px] text-slate-400 dark:text-slate-500 italic mt-1">{disclaimer}</p>
    </div>
  )
}
