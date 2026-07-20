import React from 'react'

interface TableProps {
  columns: string[]
  data: any[]
  onRowClick?: (row: any) => void
  renderRow?: (row: any, index: number) => React.ReactNode
}

export default function Table({ columns, data, onRowClick, renderRow }: TableProps) {
  if (data.length === 0) {
    return (
      <div className="empty-state">
        <svg
          className="empty-state-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <p className="empty-state-text">No data available</p>
        <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Get started by adding some entries</p>
      </div>
    )
  }

  return (
    <div className="table-container">
      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              {columns.map((column, index) => (
                <th key={index}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                onClick={() => onRowClick && onRowClick(row)}
                className={onRowClick ? 'cursor-pointer' : ''}
              >
                {renderRow ? (
                  renderRow(row, index)
                ) : (
                  Object.values(row).map((value: any, cellIndex) => (
                    <td key={cellIndex}>{String(value)}</td>
                  ))
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {data.map((row, index) => {
          // For custom renderRow, we need to extract content differently
          if (renderRow) {
            // Create a temporary container to extract cell content
            const rowContent = renderRow(row, index)
            // If it's a React fragment or array of elements, extract them
            const cells = React.isValidElement(rowContent) && rowContent.props.children
              ? React.Children.toArray(rowContent.props.children)
              : React.Children.toArray(rowContent)
            
            return (
              <div
                key={index}
                onClick={() => onRowClick && onRowClick(row)}
                className={`bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-700 shadow-sm ${
                  onRowClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
                }`}
              >
                <div className="space-y-3">
                  {columns.map((column, colIndex) => {
                    const cell = cells[colIndex]
                    // Extract content only: never render <td>/<th> inside <div> (invalid DOM)
                    let cellContent: React.ReactNode
                    if (React.isValidElement(cell) && typeof cell.type === 'string' && (cell.type === 'td' || cell.type === 'th')) {
                      cellContent = (cell.props as { children?: React.ReactNode }).children
                    } else if (React.isValidElement(cell) && cell.props && 'children' in cell) {
                      cellContent = (cell.props as { children?: React.ReactNode }).children
                    } else {
                      cellContent = cell
                    }
                    if (cellContent === undefined && React.isValidElement(cell)) {
                      cellContent = '-'
                    }
                    return (
                      <div key={colIndex} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 py-2 border-b border-gray-100 dark:border-slate-700 last:border-0">
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                          {column}:
                        </span>
                        <div className="text-sm text-gray-900 dark:text-white flex-1">
                          {cellContent ?? '-'}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          }
          
          // Default rendering for non-custom rows
          return (
            <div
              key={index}
              onClick={() => onRowClick && onRowClick(row)}
              className={`bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-700 shadow-sm ${
                onRowClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
              }`}
            >
              <div className="space-y-2">
                {Object.entries(row).map(([key, value], cellIndex) => (
                  <div key={cellIndex} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 py-2 border-b border-gray-100 dark:border-slate-700 last:border-0">
                    <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-sm text-gray-900 dark:text-white">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
