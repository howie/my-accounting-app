'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useTemplates, useApplyTemplate } from '@/lib/hooks/useTemplates'
import type { TransactionTemplateListItem } from '@/types'

export interface QuickEntryPanelProps {
  /** Ledger ID for templates */
  ledgerId: string
  /** Maximum number of templates to show (default: 6) */
  maxTemplates?: number
  /** Called after a template is successfully applied */
  onApplySuccess?: () => void
  /** Called when user wants to see all templates */
  onViewAll?: () => void
  /** Called when user wants to edit a template before saving */
  onEditTemplate?: (templateId: string) => void
}

function getTypeColor(type: string): string {
  switch (type) {
    case 'EXPENSE':
      return 'border-l-red-500'
    case 'INCOME':
      return 'border-l-green-500'
    case 'TRANSFER':
      return 'border-l-blue-500'
    default:
      return 'border-l-gray-500'
  }
}

export function QuickEntryPanel({
  ledgerId,
  maxTemplates = 6,
  onApplySuccess,
  onViewAll,
  onEditTemplate,
}: QuickEntryPanelProps) {
  const t = useTranslations()
  const [applyError, setApplyError] = useState<string | null>(null)

  const { data: templatesData, isLoading } = useTemplates(ledgerId)
  const applyTemplate = useApplyTemplate(ledgerId)

  const [confirmApply, setConfirmApply] = useState<TransactionTemplateListItem | null>(null)
  const [applyingId, setApplyingId] = useState<string | null>(null)

  const templates = (templatesData?.data ?? []).slice(0, maxTemplates)
  const totalTemplates = templatesData?.total ?? 0
  const hasMore = totalTemplates > maxTemplates

  const handleTemplateClick = (template: TransactionTemplateListItem) => {
    setConfirmApply(template)
  }

  const handleApplyConfirm = async () => {
    if (!confirmApply) return

    setApplyingId(confirmApply.id)
    setApplyError(null)
    try {
      await applyTemplate.mutateAsync({ templateId: confirmApply.id })
      setConfirmApply(null)
      onApplySuccess?.()
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : t('common.error'))
    } finally {
      setApplyingId(null)
    }
  }

  const handleApplyCancel = () => {
    setConfirmApply(null)
    setApplyError(null)
  }

  const handleEditBeforeSave = () => {
    if (confirmApply && onEditTemplate) {
      onEditTemplate(confirmApply.id)
      setConfirmApply(null)
    }
  }

  // Don't render if no ledger or no templates
  if (!ledgerId || (!isLoading && templates.length === 0)) {
    return null
  }

  return (
    <>
      <Card data-testid="quick-entry-panel">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{t('templates.quickEntry')}</CardTitle>
            {hasMore && onViewAll && (
              <Button
                variant="link"
                size="sm"
                onClick={onViewAll}
                className="text-sm"
                data-testid="view-all-templates"
              >
                {t('templates.seeAll')} ({totalTemplates})
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-4 text-muted-foreground">
              {t('common.loading')}
            </div>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => handleTemplateClick(template)}
                  disabled={applyingId === template.id}
                  className={`flex items-center justify-between rounded-lg border border-l-4 p-3 text-left transition-colors hover:bg-accent disabled:opacity-50 ${getTypeColor(template.transaction_type)}`}
                  data-testid={`quick-entry-${template.id}`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{template.name}</div>
                    <div className="text-sm text-muted-foreground">
                      ${parseFloat(template.amount).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Apply Confirmation Dialog */}
      <Dialog open={!!confirmApply} onOpenChange={() => setConfirmApply(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('templates.confirmApply')}</DialogTitle>
            <DialogDescription>
              {t('templates.confirmApplyMessage')}
            </DialogDescription>
          </DialogHeader>
          {applyError && (
            <div
              className="rounded bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              {applyError}
            </div>
          )}
          {confirmApply && (
            <div className="rounded-lg border bg-muted/50 p-4">
              <div className="mb-2 font-medium">{confirmApply.name}</div>
              <div className="space-y-1 text-sm text-muted-foreground">
                <div>
                  {t('transactionForm.typeLabel')}: {t(`transactionTypes.${confirmApply.transaction_type}`)}
                </div>
                <div>
                  {t('transactionForm.amountLabel')}: ${parseFloat(confirmApply.amount).toFixed(2)}
                </div>
                <div>
                  {t('transactionForm.descriptionLabel')}: {confirmApply.description}
                </div>
              </div>
            </div>
          )}
          <DialogFooter className="flex-col gap-2 sm:flex-row">
            <Button
              variant="outline"
              onClick={handleApplyCancel}
              data-testid="cancel-apply"
            >
              {t('common.cancel')}
            </Button>
            {onEditTemplate && (
              <Button
                variant="outline"
                onClick={handleEditBeforeSave}
                data-testid="edit-before-save"
              >
                {t('templates.editBeforeSave')}
              </Button>
            )}
            <Button
              onClick={handleApplyConfirm}
              disabled={applyTemplate.isPending}
              data-testid="confirm-apply"
            >
              {applyTemplate.isPending ? t('common.loading') : t('templates.quickSave')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
