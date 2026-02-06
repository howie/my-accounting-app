

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Eye } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { InstallmentForm } from './InstallmentForm'
import { InstallmentDetails } from './InstallmentDetails'
import { useInstallmentPlans } from '@/lib/hooks/useInstallments'
import { formatAmount } from '@/lib/utils'

export function InstallmentList() {
  const { t } = useTranslation() // We'll add installments section later
  const { data: plans, isLoading } = useInstallmentPlans()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)

  if (isLoading) {
    return <div className="p-4 text-center text-muted-foreground">{t('common.loading')}</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Installment Plans</h2>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Plan
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create Installment Plan</DialogTitle>
            </DialogHeader>
            <InstallmentForm
              onSuccess={() => setIsCreateOpen(false)}
              onCancel={() => setIsCreateOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Details Dialog */}
      <Dialog open={!!selectedPlanId} onOpenChange={(open) => !open && setSelectedPlanId(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Plan Details</DialogTitle>
          </DialogHeader>
          {selectedPlanId && <InstallmentDetails planId={selectedPlanId} />}
        </DialogContent>
      </Dialog>

      <div className="rounded-md border">
        {(!plans || plans.length === 0) ? (
          <div className="p-8 text-center text-muted-foreground">No installment plans yet</div>
        ) : (
          <div className="divide-y">
            <div className="flex items-center bg-muted/50 px-4 py-3 text-sm font-medium">
              <div className="flex-1">{t('recurring.table.name')}</div>
              <div className="w-32 text-right">Total Amount</div>
              <div className="w-24 text-right">Count</div>
              <div className="w-32 text-right">Start Date</div>
              <div className="w-16"></div>
            </div>
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="flex items-center px-4 py-3 hover:bg-muted/30 transition-colors"
              >
                <div className="flex flex-1 items-center gap-3">
                  <span className="font-medium">{plan.name}</span>
                </div>
                <div className="w-32 text-right font-mono">
                  ${formatAmount(plan.total_amount.toString())}
                </div>
                <div className="w-24 text-right">
                  {plan.installment_count}
                </div>
                <div className="w-32 text-right text-sm text-muted-foreground">
                  {plan.start_date}
                </div>
                <div className="w-16 flex justify-end">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedPlanId(plan.id)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
