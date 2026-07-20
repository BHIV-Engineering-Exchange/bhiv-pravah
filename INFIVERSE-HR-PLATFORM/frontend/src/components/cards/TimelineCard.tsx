import type { TimelineEvent } from './types'
import { cardShellClassName } from './cardStyles'

interface TimelineCardProps {
  title: string
  events: TimelineEvent[]
  readOnly?: boolean
  className?: string
}

function statusClass(status?: TimelineEvent['status']) {
  if (status === 'success') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (status === 'failure') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
  return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
}

export default function TimelineCard({ title, events, readOnly = true, className = '' }: TimelineCardProps) {
  return (
    <div className={cardShellClassName('normal', className)} aria-readonly={readOnly}>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{title}</p>
      <ul className="mt-2 space-y-2 max-h-48 overflow-y-auto">
        {events.length === 0 ? (
          <li className="text-xs text-slate-400">No timeline events</li>
        ) : (
          events.map((event) => (
            <li key={event.id} className="flex items-start gap-2 text-xs">
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold ${statusClass(event.status)}`}>
                {event.status || 'in_progress'}
              </span>
              <div className="min-w-0">
                <p className="font-medium text-slate-700 dark:text-slate-200 truncate">{event.label}</p>
                <p className="text-slate-400">{event.timestamp}</p>
                {event.detail && <p className="text-slate-500 truncate">{event.detail}</p>}
              </div>
            </li>
          ))
        )}
      </ul>
      <p className="text-[10px] text-slate-400 italic mt-2">Chronological audit visibility — not mutating state</p>
    </div>
  )
}
