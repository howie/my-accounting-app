import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, startOfMonth, endOfMonth } from 'date-fns'
import { Loader2 } from 'lucide-react'

import { ReportTable } from '@/components/reports/ReportTable'
import { IncomeExpenseBreakdownChart } from '@/components/reports/IncomeExpenseBreakdownChart'
import { Button } from '@/components/ui/button'
import { DateRangePicker } from '@/components/ui/DateRangePicker'
import { apiGet } from '@/lib/api'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { IncomeStatement } from '@/types/reports'

export default function IncomeStatementPage() {
  const { currentLedger } = useLedgerContext()
  const [startDate, setStartDate] = useState<Date>(startOfMonth(new Date()))
  const [endDate, setEndDate] = useState<Date>(endOfMonth(new Date()))

  const { data, isLoading, error } = useQuery({
    queryKey: [
      'income-statement',
      currentLedger?.id,
      startDate ? format(startDate, 'yyyy-MM-dd') : '',
      endDate ? format(endDate, 'yyyy-MM-dd') : '',
    ],
    queryFn: async () => {
      if (!currentLedger || !startDate || !endDate) return null
      return apiGet<IncomeStatement>(
        `/reports/income-statement?ledger_id=${currentLedger.id}&start_date=${format(
          startDate,
          'yyyy-MM-dd'
        )}&end_date=${format(endDate, 'yyyy-MM-dd')}`
      )
    },
    enabled: !!currentLedger && !!startDate && !!endDate,
  })

  if (!currentLedger) {
    return <div className="p-8">Please select a ledger.</div>
  }

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Income Statement</h1>
          <p className="text-muted-foreground">
            Financial performance for {startDate ? format(startDate, 'MMM d, yyyy') : '...'} -{' '}
            {endDate ? format(endDate, 'MMM d, yyyy') : '...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={(date) => date && setStartDate(date)}
            onEndDateChange={(date) => date && setEndDate(date)}
          />
          <Button variant="outline" onClick={() => window.print()}>
            Print
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (currentLedger && startDate && endDate) {
                const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'}/reports/income-statement/export?ledger_id=${currentLedger.id}&start_date=${format(startDate, 'yyyy-MM-dd')}&end_date=${format(endDate, 'yyyy-MM-dd')}&format=csv`
                window.open(url, '_blank')
              }
            }}
          >
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (currentLedger && startDate && endDate) {
                const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'}/reports/income-statement/export?ledger_id=${currentLedger.id}&start_date=${format(startDate, 'yyyy-MM-dd')}&end_date=${format(endDate, 'yyyy-MM-dd')}&format=html`
                window.open(url, '_blank')
              }
            }}
          >
            Export HTML
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-[400px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="rounded-md bg-destructive/15 p-4 text-destructive">
          Error loading report: {(error as Error).message}
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* Breakdown Charts */}
          <div className="grid gap-6 md:grid-cols-2">
            <IncomeExpenseBreakdownChart
              title="Income"
              data={data.income}
              total={data.total_income}
              color="amber"
            />
            <IncomeExpenseBreakdownChart
              title="Expenses"
              data={data.expenses}
              total={data.total_expenses}
              color="rose"
            />
          </div>

          {/* Detail Tables */}
          <div className="grid gap-6 md:grid-cols-2">
            <ReportTable
              title="Income"
              total={data.total_income}
              data={data.income}
            />
            <ReportTable
              title="Expenses"
              total={data.total_expenses}
              data={data.expenses}
            />
          </div>

          <div className="flex items-center justify-between rounded-md border bg-muted/50 px-4 py-3 font-bold">
            <span>Net Income</span>
            <span
              className={
                parseFloat(data.net_income) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }
            >
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
              }).format(parseFloat(data.net_income))}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  )
}
