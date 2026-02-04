

import { Card, BarChart } from '@tremor/react'
import type { MonthlyTrend } from '@/types/dashboard'

interface TrendChartProps {
  trends: MonthlyTrend[]
  isLoading?: boolean
}

/**
 * Bar chart showing 6-month income and expense trends.
 * Mirauve-style with green for income, purple for expenses.
 */
export function TrendChart({ trends, isLoading }: TrendChartProps) {
  const hasData = trends.some((t) => t.income > 0 || t.expenses > 0)

  // Transform data for Tremor BarChart
  const chartData = trends.map((t) => ({
    month: `${t.month} ${t.year}`,
    Income: t.income,
    Expenses: t.expenses,
  }))

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="mb-4 h-4 w-32 rounded bg-gray-200" />
          <div className="h-64 rounded bg-gray-200" />
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h3 className="mb-4 text-sm font-medium text-gray-500 dark:text-gray-400">
        Monthly Trends (Last 12 Months)
      </h3>

      {hasData ? (
        <BarChart
          data={chartData}
          index="month"
          categories={['Income', 'Expenses']}
          colors={['amber', 'rose']}
          className="h-64"
          showAnimation
          showLegend
          showGridLines={false}
          valueFormatter={formatCurrency}
          yAxisWidth={80}
        />
      ) : (
        <div className="flex h-64 items-center justify-center text-gray-400">
          <p>Not enough data to show trends</p>
        </div>
      )}
    </Card>
  )
}
