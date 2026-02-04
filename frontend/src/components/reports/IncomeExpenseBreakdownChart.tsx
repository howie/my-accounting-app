

import { Card, BarList } from '@tremor/react'
import type { ReportEntry } from '@/types/reports'

interface IncomeExpenseBreakdownChartProps {
  title: string
  data: ReportEntry[]
  total: string
  color: 'amber' | 'rose'
}

/**
 * Bar list showing breakdown of income or expense categories.
 * Shows distribution across different account categories.
 */
export function IncomeExpenseBreakdownChart({
  title,
  data,
  total,
  color,
}: IncomeExpenseBreakdownChartProps) {
  // Flatten to get top-level accounts with their amounts
  const chartData = data
    .map((entry) => ({
      name: entry.name,
      value: Math.abs(parseFloat(entry.amount)),
    }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 8) // Show top 8 categories

  const totalValue = Math.abs(parseFloat(total))
  const hasData = chartData.length > 0 && totalValue > 0

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPercent = (value: number) => {
    const percent = (value / totalValue) * 100
    return `${percent.toFixed(1)}%`
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
          {title} Breakdown
        </h3>
        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {formatCurrency(totalValue)}
        </span>
      </div>

      {hasData ? (
        <div className="space-y-4">
          <BarList
            data={chartData.map((item) => ({
              ...item,
              href: undefined,
            }))}
            valueFormatter={(value: number) => `${formatCurrency(value)} (${formatPercent(value)})`}
            color={color}
            showAnimation
          />
        </div>
      ) : (
        <div className="flex h-32 items-center justify-center text-gray-400">
          <p>No data for this period</p>
        </div>
      )}
    </Card>
  )
}
