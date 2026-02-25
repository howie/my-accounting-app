import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useDashboard } from '@/lib/hooks/useDashboard'
import { SummaryCards } from './SummaryCards'
import { IncomeExpenseChart } from './IncomeExpenseChart'
import { TrendChart } from './TrendChart'
import { QuickEntryPanel } from '@/components/templates'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { AlertCircle } from 'lucide-react'
import { DateRangePicker } from '@/components/ui/DateRangePicker'
import { RecurringAlerts } from './RecurringAlerts'

/**
 * Main dashboard grid layout.
 * Displays balance overview, income/expense chart, and trends.
 */
export function DashboardGrid() {
  const { t } = useTranslation()
  const { currentLedger } = useLedgerContext()
  const [startDate, setStartDate] = useState<Date | undefined>()
  const [endDate, setEndDate] = useState<Date | undefined>()
  const [hasInitialized, setHasInitialized] = useState(false)

  const { data, isLoading, error } = useDashboard({ startDate, endDate })

  // Initialize date range from server default if not set
  useEffect(() => {
    if (data?.dateRange && !hasInitialized) {
      setStartDate(new Date(data.dateRange.start))
      setEndDate(new Date(data.dateRange.end))
      setHasInitialized(true)
    }
  }, [data, hasInitialized])

  // No ledger selected
  if (!currentLedger) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-gray-500">
        <AlertCircle className="mb-4 h-12 w-12 text-gray-400" />
        <h2 className="text-lg font-medium">{t('dashboard.noLedger')}</h2>
        <p className="text-sm">{t('dashboard.noLedgerDesc')}</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-red-500">
        <AlertCircle className="mb-4 h-12 w-12" />
        <h2 className="text-lg font-medium">{t('dashboard.errorLoading')}</h2>
        <p className="text-sm">{error.message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('dashboard.title')}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t('dashboard.overview', { name: currentLedger.name })}
          </p>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
        />
      </div>

      <RecurringAlerts />

      {/* Summary Cards Row */}
      <SummaryCards
        totalAssets={data?.totalAssets ?? 0}
        totalLiabilities={data?.totalLiabilities ?? 0}
        income={data?.currentMonth.income ?? 0}
        expenses={data?.currentMonth.expenses ?? 0}
        isLoading={isLoading}
      />

      {/* Trend Chart - Full Width */}
      <TrendChart trends={data?.trends ?? []} isLoading={isLoading} />

      {/* Bottom Row: Income/Expense Split & Quick Entry */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <IncomeExpenseChart
          income={data?.currentMonth.income ?? 0}
          expenses={data?.currentMonth.expenses ?? 0}
          isLoading={isLoading}
        />
        <QuickEntryPanel ledgerId={currentLedger.id} />
      </div>
    </div>
  )
}
