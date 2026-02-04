

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check, X, Calendar } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { useApproveRecurringTransaction } from '@/lib/hooks/useRecurring'
import { formatAmount } from '@/lib/utils'
import type { RecurringTransactionDue } from '@/services/recurring'

interface ApprovalModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dueItems: RecurringTransactionDue[]
}

export function ApprovalModal({ open, onOpenChange, dueItems }: ApprovalModalProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'recurring' })
  const approveMutation = useApproveRecurringTransaction()
  const [approvingId, setApprovingId] = useState<string | null>(null)

  const handleApprove = async (id: string, dueDate: string) => {
    setApprovingId(id)
    try {
      await approveMutation.mutateAsync({ id, date: dueDate })
      // If no more items, close modal automatically
      if (dueItems.length <= 1) {
        onOpenChange(false)
      }
    } catch (err) {
      console.error('Failed to approve:', err)
    } finally {
      setApprovingId(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t('approval.title')}</DialogTitle>
          <DialogDescription>{t('approval.description')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto">
          {dueItems.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between rounded-lg border p-4 shadow-sm"
            >
              <div className="flex flex-col gap-1">
                <span className="font-semibold">{item.name}</span>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  <span>{item.due_date}</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-mono font-medium">${formatAmount(item.amount.toString())}</span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleApprove(item.id, item.due_date)}
                    disabled={approvingId === item.id || approveMutation.isPending}
                  >
                    {approvingId === item.id ? (
                        t('common.processing') // Use common loading text
                    ) : (
                      <>
                        <Check className="mr-1 h-3 w-3" />
                        {t('approval.approve')}
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          ))}
          {dueItems.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
                {t('approval.allDone')}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
