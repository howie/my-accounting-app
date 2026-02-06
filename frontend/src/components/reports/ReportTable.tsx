

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ReportEntry } from '@/types/reports'

interface ReportTableProps {
  data: ReportEntry[]
  title?: string
  total?: string
  className?: string
}

export function ReportTable({ data, title, total, className }: ReportTableProps) {
  return (
    <div className={cn('rounded-md border', className)}>
      {title && (
        <div className="flex items-center justify-between bg-muted/50 px-4 py-3 font-medium">
          <span>{title}</span>
          {total && <span>{formatCurrency(total)}</span>}
        </div>
      )}
      <div className="divide-y">
        {data.map((entry) => (
          <ReportRow key={entry.account_id || entry.name} entry={entry} />
        ))}
      </div>
    </div>
  )
}

function ReportRow({ entry }: { entry: ReportEntry }) {
  const [isOpen, setIsOpen] = useState(true)
  const hasChildren = entry.children && entry.children.length > 0

  return (
    <div>
      <div
        className={cn(
          'flex items-center justify-between px-4 py-2 hover:bg-muted/50',
          entry.level === 0 && 'font-medium',
          entry.level > 0 && 'text-sm'
        )}
        style={{ paddingLeft: `${(entry.level * 1.5) + 1}rem` }}
      >
        <div className="flex items-center gap-2">
          {hasChildren ? (
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="h-4 w-4 text-muted-foreground hover:text-foreground"
            >
              {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
          ) : (
            <div className="h-4 w-4" /> // Spacer
          )}
          <span>{entry.name}</span>
        </div>
        <span className={cn(
            parseFloat(entry.amount) < 0 && 'text-red-500'
        )}>
            {formatCurrency(entry.amount)}
        </span>
      </div>
      {hasChildren && isOpen && (
        <div>
          {entry.children.map((child) => (
            <ReportRow key={child.account_id || child.name} entry={child} />
          ))}
        </div>
      )}
    </div>
  )
}

function formatCurrency(amount: string) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(parseFloat(amount))
}
