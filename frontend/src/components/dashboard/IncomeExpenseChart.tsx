'use client'

import { Card, DonutChart, Legend } from '@tremor/react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface IncomeExpenseChartProps {
  income: number
  expenses: number
  isLoading?: boolean
}

/**
 * Donut chart showing income vs expense breakdown for current month.
 * Mirauve-style with green for income, purple for expenses.
 */
export function IncomeExpenseChart({ income, expenses, isLoading }: IncomeExpenseChartProps) {
  const netCashFlow = income - expenses
  const hasData = income > 0 || expenses > 0

  const chartData = [
    { name: 'Income', value: income },
    { name: 'Expenses', value: expenses },
  ]

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
          <div className="h-48 rounded bg-gray-200" />
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h3 className="mb-4 text-sm font-medium text-gray-500 dark:text-gray-400">
        Income vs Expenses
      </h3>

      {hasData ? (
        <>
          <DonutChart
            data={chartData}
            category="value"
            index="name"
            colors={['emerald', 'fuchsia']}
            className="h-48"
            showAnimation
            showTooltip
            valueFormatter={formatCurrency}
          />

          <Legend
            categories={['Income', 'Expenses']}
            colors={['emerald', 'fuchsia']}
            className="mt-4 justify-center"
          />

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-500" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Income</p>
                <p className="text-sm font-semibold text-emerald-600">{formatCurrency(income)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-fuchsia-500" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Expenses</p>
                <p className="text-sm font-semibold text-fuchsia-600">{formatCurrency(expenses)}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">Net Cash Flow</span>
              <span
                className={`text-lg font-bold ${
                  netCashFlow >= 0 ? 'text-emerald-600' : 'text-red-600'
                }`}
              >
                {netCashFlow >= 0 ? '+' : ''}
                {formatCurrency(netCashFlow)}
              </span>
            </div>
          </div>
        </>
      ) : (
        <div className="flex h-48 items-center justify-center text-gray-400">
          <p>No transactions this month</p>
        </div>
      )}
    </Card>
  )
}
