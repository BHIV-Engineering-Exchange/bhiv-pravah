import type { MapNode } from './types'
import { cardShellClassName } from './cardStyles'

interface MapCardProps {
  title: string
  nodes: MapNode[]
  readOnly?: boolean
  className?: string
}

function renderNode(node: MapNode, depth = 0) {
  return (
    <li key={node.id} className="text-xs" style={{ marginLeft: depth * 12 }}>
      <span className="font-medium text-slate-700 dark:text-slate-200">{node.label}</span>
      {node.level && <span className="text-slate-400 ml-1">({node.level})</span>}
      {node.children && node.children.length > 0 && (
        <ul className="mt-1 space-y-1">{node.children.map((child) => renderNode(child, depth + 1))}</ul>
      )}
    </li>
  )
}

export default function MapCard({ title, nodes, readOnly = true, className = '' }: MapCardProps) {
  return (
    <div className={cardShellClassName('normal', className)} aria-readonly={readOnly}>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{title}</p>
      <ul className="mt-2 space-y-1 max-h-48 overflow-y-auto">{nodes.map((node) => renderNode(node))}</ul>
      <p className="text-[10px] text-slate-400 italic mt-2">Hierarchy map — structural visibility, not org mutation</p>
    </div>
  )
}
