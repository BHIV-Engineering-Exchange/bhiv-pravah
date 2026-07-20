export type CardSeverity = 'normal' | 'warning' | 'alert'

export interface ConstitutionalCardProps {
  label: string
  value: string | number
  sublabel?: string
  delta?: string
  deltaPositive?: boolean
  severity?: CardSeverity
  sourceSystem?: string
  correlationId?: string
  readOnly?: boolean
  disclaimer?: string
  className?: string
}

export interface TimelineEvent {
  id: string
  timestamp: string
  label: string
  status?: 'success' | 'failure' | 'in_progress'
  detail?: string
}

export interface MapNode {
  id: string
  label: string
  level?: string
  children?: MapNode[]
}
