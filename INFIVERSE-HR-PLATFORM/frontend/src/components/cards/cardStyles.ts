import type { CardSeverity } from './types'

export const OBSERVABILITY_DISCLAIMER = 'Observability only — not execution authority'

export function severityClasses(severity: CardSeverity = 'normal') {
  const borderColor =
    severity === 'alert'
      ? 'border-red-400/40 dark:border-red-500/30'
      : severity === 'warning'
        ? 'border-amber-400/40 dark:border-amber-500/30'
        : 'border-white/10 dark:border-slate-700/50'

  const bgColor =
    severity === 'alert'
      ? 'bg-red-50/80 dark:bg-red-950/30'
      : severity === 'warning'
        ? 'bg-amber-50/80 dark:bg-amber-950/30'
        : 'bg-white/70 dark:bg-slate-800/60'

  const valueColor =
    severity === 'alert'
      ? 'text-red-600 dark:text-red-400'
      : severity === 'warning'
        ? 'text-amber-600 dark:text-amber-400'
        : 'text-slate-900 dark:text-white'

  return { borderColor, bgColor, valueColor }
}

export function cardShellClassName(severity: CardSeverity = 'normal', className = '') {
  const { borderColor, bgColor } = severityClasses(severity)
  return `rounded-2xl border ${borderColor} ${bgColor} backdrop-blur-md p-4 flex flex-col gap-1 shadow-sm hover:shadow-md transition-shadow ${className}`.trim()
}
