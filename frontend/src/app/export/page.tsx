'use client'

import { useState } from 'react'
import { FileText, FileSpreadsheet, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { DateRangePicker } from '@/components/ui/DateRangePicker'
import { exportTransactions } from '@/lib/api/export'
import { format } from 'date-fns'

export default function ExportPage() {
  const [formatType, setFormatType] = useState<'csv' | 'html'>('csv')
  const [startDate, setStartDate] = useState<Date | undefined>(undefined)
  const [endDate, setEndDate] = useState<Date | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)

  const handleExport = async () => {
    try {
      setIsLoading(true)
      await exportTransactions({
        format: formatType,
        start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
        end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
      })
    } catch (error) {
      console.error('Export failed', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-10 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
          <CardDescription>
            Download your transaction history for backup, external analysis, or printing.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-8">

          {/* Format Selection */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium">1. Choose Format</h3>
            <div className="grid grid-cols-2 gap-4">
              <label className={`flex flex-col items-center justify-between rounded-lg border-2 p-4 hover:bg-accent hover:text-accent-foreground cursor-pointer ${formatType === 'csv' ? 'border-primary bg-accent' : 'border-muted bg-transparent'}`}>
                <input
                  type="radio"
                  name="format"
                  value="csv"
                  className="sr-only"
                  checked={formatType === 'csv'}
                  onChange={() => setFormatType('csv')}
                />
                <FileSpreadsheet className="mb-3 h-6 w-6" />
                <div className="text-center">
                    <span className="block font-semibold">CSV</span>
                    <span className="text-xs text-muted-foreground">For Excel & Backup</span>
                </div>
              </label>

              <label className={`flex flex-col items-center justify-between rounded-lg border-2 p-4 hover:bg-accent hover:text-accent-foreground cursor-pointer ${formatType === 'html' ? 'border-primary bg-accent' : 'border-muted bg-transparent'}`}>
                <input
                  type="radio"
                  name="format"
                  value="html"
                  className="sr-only"
                  checked={formatType === 'html'}
                  onChange={() => setFormatType('html')}
                />
                <FileText className="mb-3 h-6 w-6" />
                <div className="text-center">
                    <span className="block font-semibold">HTML</span>
                    <span className="text-xs text-muted-foreground">For Printing</span>
                </div>
              </label>
            </div>
          </div>

          {/* Date Range */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium">2. Select Date Range (Optional)</h3>
            <div className="flex flex-col gap-2">
                <DateRangePicker
                startDate={startDate}
                endDate={endDate}
                onStartDateChange={setStartDate}
                onEndDateChange={setEndDate}
                className="w-full justify-start"
                />
                <p className="text-xs text-muted-foreground">Leave empty to export all data.</p>
            </div>
          </div>

        </CardContent>
        <CardFooter className="flex justify-end">
          <Button onClick={handleExport} disabled={isLoading} className="w-full sm:w-auto gap-2">
            <Download className="h-4 w-4" />
            {isLoading ? 'Exporting...' : 'Export Transactions'}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
