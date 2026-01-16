'use client'

import { useState } from 'react'
import { Download, FileText, FileSpreadsheet } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { DateRangePicker } from '@/components/ui/DateRangePicker'
import { exportTransactions } from '@/lib/api/export'
import { format } from 'date-fns'

// Need to check if Label and RadioGroup exist or use native elements.
// I will assume standard HTML for now to be safe if components are missing,
// or I'll check existence. I'll stick to native for simplicity if uncertain.
// Actually, let's check components.

interface ExportModalProps {
  children?: React.ReactNode
  preSelectedAccountId?: string
}

export function ExportModal({ children, preSelectedAccountId }: ExportModalProps) {
  const [open, setOpen] = useState(false)
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
        account_id: preSelectedAccountId
      })
      setOpen(false)
    } catch (error) {
      console.error('Export failed', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            Export Data
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Export Data</DialogTitle>
          <DialogDescription>
            Download your transactions for backup or analysis.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Format Selection */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium leading-none">Format</h4>
            <div className="flex gap-4">
              <label className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-md border p-4 text-sm font-medium transition-all hover:bg-accent ${formatType === 'csv' ? 'border-primary bg-accent text-accent-foreground' : 'text-muted-foreground'}`}>
                <input
                  type="radio"
                  name="format"
                  value="csv"
                  className="sr-only"
                  checked={formatType === 'csv'}
                  onChange={() => setFormatType('csv')}
                />
                <FileSpreadsheet className="h-5 w-5" />
                CSV (Excel)
              </label>

              <label className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-md border p-4 text-sm font-medium transition-all hover:bg-accent ${formatType === 'html' ? 'border-primary bg-accent text-accent-foreground' : 'text-muted-foreground'}`}>
                <input
                  type="radio"
                  name="format"
                  value="html"
                  className="sr-only"
                  checked={formatType === 'html'}
                  onChange={() => setFormatType('html')}
                />
                <FileText className="h-5 w-5" />
                HTML (Print)
              </label>
            </div>
          </div>

          {/* Date Range */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium leading-none">Date Range (Optional)</h4>
            <DateRangePicker
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
              className="justify-between"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleExport} disabled={isLoading}>
            {isLoading ? 'Exporting...' : 'Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
