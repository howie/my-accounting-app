'use client'

import { Card, DonutChart, Legend } from '@tremor/react'
import type { ReportEntry } from '@/types/reports'

interface BalanceBreakdownChartProps {
  title: string
  data: ReportEntry[]
  total: string
  color: 'blue' | 'emerald' | 'amber' | 'rose'
}

/**
 * Donut chart showing breakdown of balance sheet categories.
 * Shows top-level account distribution (e.g., Cash, Investments, etc.)
 */
export function BalanceBreakdownChart({
  title,
  data,
  total,
  color,
}: BalanceBreakdownChartProps) {
  // Flatten to get top-level accounts with their amounts
  const chartData = data
    .map((entry) => ({
      name: entry.name,
      value: Math.abs(parseFloat(entry.amount)),
    }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 6) // Show top 6 categories

  const totalValue = parseFloat(total)
  const hasData = chartData.length > 0 && totalValue > 0

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const colorVariants = {
    blue: ['blue', 'cyan', 'indigo', 'sky', 'violet', 'slate'],
    emerald: ['emerald', 'green', 'teal', 'lime', 'cyan', 'slate'],
    amber: ['amber', 'yellow', 'orange', 'lime', 'green', 'slate'],
    rose: ['rose', 'pink', 'red', 'orange', 'fuchsia', 'slate'],
  }

  return (
    <Card className="p-6">
      <h3 className="mb-4 text-sm font-medium text-gray-500 dark:text-gray-400">
        {title} Breakdown
      </h3>

      {hasData ? (
        <div className="space-y-4">
          <DonutChart
            data={chartData}
            category="value"
            index="name"
            colors={colorVariants[color] as never}
            className="h-48"
            showAnimation
            valueFormatter={formatCurrency}
          />
          <Legend
            categories={chartData.map((d) => d.name)}
            colors={colorVariants[color] as never}
            className="mt-4 justify-center"
          />
        </div>
      ) : (
        <div className="flex h-48 items-center justify-center text-gray-400">
          <p>No data available</p>
        </div>
      )}
    </Card>
  )
}
