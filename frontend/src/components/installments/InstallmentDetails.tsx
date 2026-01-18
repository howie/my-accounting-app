'use client'

import { useTranslations } from 'next-intl'
import { format } from 'date-fns'

import { useInstallmentPlan, useInstallmentTransactions } from '@/lib/hooks/useInstallments'
import { formatAmount } from '@/lib/utils'

interface InstallmentDetailsProps {
  planId: string
}

export function InstallmentDetails({ planId }: InstallmentDetailsProps) {
  const t = useTranslations()
  const { data: plan, isLoading: isPlanLoading } = useInstallmentPlan(planId)
  const { data: transactions, isLoading: isTxnLoading } = useInstallmentTransactions(planId)

  if (isPlanLoading || isTxnLoading) {
    return <div className="p-4 text-center">{t('common.loading')}</div>
  }

  if (!plan) {
    return <div className="p-4 text-center text-destructive">Plan not found</div>
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 rounded-lg border p-4 text-sm">
        <div>
          <div className="text-muted-foreground">Plan Name</div>
          <div className="font-medium">{plan.name}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Total Amount</div>
          <div className="font-medium">${formatAmount(plan.total_amount.toString())}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Installments</div>
          <div className="font-medium">{plan.installment_count} Months</div>
        </div>
        <div>
          <div className="text-muted-foreground">Start Date</div>
          <div className="font-medium">{format(new Date(plan.start_date), 'yyyy-MM-dd')}</div>
        </div>
      </div>

      <div>
        <h3 className="mb-2 font-medium">Payment Schedule</h3>
        <div className="rounded-md border">
          <div className="divide-y">
            {/* Header */}
            <div className="flex items-center bg-muted/50 px-4 py-3 text-sm font-medium">
              <div className="w-12 text-center">#</div>
              <div className="w-32">Date</div>
              <div className="flex-1">Description</div>
              <div className="w-32 text-right">Amount</div>
              <div className="w-24 text-center">Status</div>
            </div>

            {/* Rows */}
            {transactions?.map((txn, index) => {
              const isFuture = new Date(txn.date) > new Date()
              return (
                <div key={txn.id} className="flex items-center px-4 py-3 text-sm">
                  <div className="w-12 text-center font-medium">{index + 1}</div>
                  <div className="w-32">{format(new Date(txn.date), 'yyyy-MM-dd')}</div>
                  <div className="flex-1 truncate pr-4">{txn.description}</div>
                  <div className="w-32 text-right font-mono">
                    {formatAmount(txn.amount)}
                  </div>
                  <div className="w-24 text-center">
                    {isFuture ? (
                      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80">
                        Scheduled
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground hover:bg-primary/80">
                        Posted
                      </span>
                    )}
                  </div>
                </div>
              )
            })}

            {(!transactions || transactions.length === 0) && (
              <div className="p-4 text-center text-muted-foreground">
                No transactions found
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
