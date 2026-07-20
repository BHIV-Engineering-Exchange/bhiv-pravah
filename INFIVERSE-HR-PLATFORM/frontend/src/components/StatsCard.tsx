import ExecutiveMetricCard from './cards/ExecutiveMetricCard'

interface CardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  color?: string
  trend?: { value: number; label: string }
}

/** @deprecated Use ExecutiveMetricCard from components/cards directly. Thin adapter for portal dashboards. */
export default function StatsCard({ title, value, icon, trend }: CardProps) {
  const delta = trend ? `${trend.value >= 0 ? '+' : ''}${trend.value}% ${trend.label}` : undefined
  return (
    <div className="relative">
      <ExecutiveMetricCard
        label={title}
        value={value}
        delta={delta}
        deltaPositive={trend ? trend.value >= 0 : undefined}
        sourceSystem="portal-dashboard"
        readOnly
      />
      {icon && (
        <div className="absolute top-4 right-4 w-10 h-10 rounded-xl flex items-center justify-center opacity-80 pointer-events-none">
          {icon}
        </div>
      )}
    </div>
  )
}
