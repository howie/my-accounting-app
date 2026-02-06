

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Bell, Check } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useDueRecurringTransactions } from '@/lib/hooks/useRecurring'
import { ApprovalModal } from '@/components/recurring/ApprovalModal'

export function RecurringAlerts() {
  const { t } = useTranslation(undefined, { keyPrefix: 'recurring' })
  const { data: dueItems, isLoading } = useDueRecurringTransactions()
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (isLoading || !dueItems || dueItems.length === 0) {
    return null
  }

  return (
    <>
      <div className="mb-6 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900 dark:border-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
        <div className="flex items-center gap-3">
          <Bell className="h-5 w-5 animate-pulse" />
          <span className="font-medium">
            {t('alerts.dueMessage', { count: dueItems.length })}
          </span>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-amber-300 bg-white hover:bg-amber-50 dark:border-amber-800 dark:bg-transparent dark:hover:bg-amber-900/40"
          onClick={() => setIsModalOpen(true)}
        >
          {t('alerts.review')}
        </Button>
      </div>

      <ApprovalModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        dueItems={dueItems}
      />
    </>
  )
}
