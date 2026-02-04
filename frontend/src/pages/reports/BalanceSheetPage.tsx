import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Loader2 } from 'lucide-react'

import { ReportTable } from '@/components/reports/ReportTable'
import { BalanceBreakdownChart } from '@/components/reports/BalanceBreakdownChart'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiGet } from '@/lib/api'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { BalanceSheet } from '@/types/reports'

export default function BalanceSheetPage() {
  const { currentLedger } = useLedgerContext()
  const [date, setDate] = useState(new Date())

  const { data, isLoading, error } = useQuery({
    queryKey: ['balance-sheet', currentLedger?.id, format(date, 'yyyy-MM-dd')],
    queryFn: async () => {
      if (!currentLedger) return null
      return apiGet<BalanceSheet>(
        `/reports/balance-sheet?ledger_id=${currentLedger.id}&date=${format(date, 'yyyy-MM-dd')}`
      )
    },
    enabled: !!currentLedger,
  })

  if (!currentLedger) {
    return <div className="p-8">Please select a ledger.</div>
  }

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Balance Sheet</h1>
          <p className="text-muted-foreground">
            Financial position as of {format(date, 'MMMM d, yyyy')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={format(date, 'yyyy-MM-dd')}
            onChange={(e) => {
              if (e.target.value) {
                setDate(new Date(e.target.value))
              }
            }}
            className="w-[160px]"
          />
          <Button variant="outline" onClick={() => window.print()}>
            Print
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (currentLedger) {
                const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'}/reports/balance-sheet/export?ledger_id=${currentLedger.id}&date=${format(date, 'yyyy-MM-dd')}&format=csv`
                window.open(url, '_blank')
              }
            }}
          >
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              if (currentLedger) {
                const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'}/reports/balance-sheet/export?ledger_id=${currentLedger.id}&date=${format(date, 'yyyy-MM-dd')}&format=html`
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
          <div className="grid gap-6 md:grid-cols-3">
            <BalanceBreakdownChart
              title="Assets"
              data={data.assets}
              total={data.total_assets}
              color="emerald"
            />
            <BalanceBreakdownChart
              title="Liabilities"
              data={data.liabilities}
              total={data.total_liabilities}
              color="rose"
            />
            <BalanceBreakdownChart
              title="Equity"
              data={data.equity}
              total={data.total_equity}
              color="blue"
            />
          </div>

          {/* Detail Tables */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-6">
              <ReportTable
                title="Assets"
                total={data.total_assets}
                data={data.assets}
              />
            </div>
            <div className="space-y-6">
              <ReportTable
                title="Liabilities"
                total={data.total_liabilities}
                data={data.liabilities}
              />
              <ReportTable
                title="Equity"
                total={data.total_equity}
                data={data.equity}
              />
              <div className="flex items-center justify-between rounded-md border bg-muted/50 px-4 py-3 font-bold">
                <span>Total Liabilities & Equity</span>
                <span>
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                  }).format(
                    parseFloat(data.total_liabilities) + parseFloat(data.total_equity)
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
