

import { Card, BarList } from '@tremor/react'


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
        <div className="mt-4">
          <BarList
            data={chartData}
            valueFormatter={formatCurrency}
            color={['amber-400', 'rose-400']}
            showAnimation
          />

          <div className="mt-6 border-t border-gray-200 pt-4 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Net Cash Flow</span>
              <span
                className={`text-lg font-bold ${netCashFlow >= 0 ? 'text-amber-600 dark:text-amber-500' : 'text-rose-600 dark:text-rose-500'
                  }`}
              >
                {netCashFlow >= 0 ? '+' : ''}
                {formatCurrency(netCashFlow)}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex h-48 items-center justify-center text-gray-400">
          <p>No transactions this month</p>
        </div>
      )}
    </Card>
  )
}
