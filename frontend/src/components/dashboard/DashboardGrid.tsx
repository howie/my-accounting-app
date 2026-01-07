'use client'

import { useDashboard } from '@/lib/hooks/useDashboard'
import { BalanceCard } from './BalanceCard'
import { IncomeExpenseChart } from './IncomeExpenseChart'
import { TrendChart } from './TrendChart'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { AlertCircle } from 'lucide-react'

/**
 * Main dashboard grid layout.
 * Displays balance overview, income/expense chart, and trends.
 */
export function DashboardGrid() {
  const { currentLedger } = useLedgerContext()
  const { data, isLoading, error } = useDashboard()

  // No ledger selected
  if (!currentLedger) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <AlertCircle className="h-12 w-12 mb-4 text-gray-400" />
        <h2 className="text-lg font-medium">No Ledger Selected</h2>
        <p className="text-sm">Please select or create a ledger to view your dashboard.</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-red-500">
        <AlertCircle className="h-12 w-12 mb-4" />
        <h2 className="text-lg font-medium">Error Loading Dashboard</h2>
        <p className="text-sm">{error.message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Financial overview for {currentLedger.name}
        </p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Balance Card - Full width on mobile, half on desktop */}
        <BalanceCard
          totalAssets={data?.totalAssets ?? 0}
          isLoading={isLoading}
        />

        {/* Income/Expense Chart */}
        <IncomeExpenseChart
          income={data?.currentMonth.income ?? 0}
          expenses={data?.currentMonth.expenses ?? 0}
          isLoading={isLoading}
        />
      </div>

      {/* Trend Chart - Full width */}
      <TrendChart trends={data?.trends ?? []} isLoading={isLoading} />
    </div>
  )
}
