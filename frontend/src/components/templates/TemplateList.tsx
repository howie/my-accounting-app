

import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { TemplateCard } from '@/components/templates/TemplateCard'
import { useTemplates, useDeleteTemplate, useApplyTemplate } from '@/lib/hooks/useTemplates'
import type { TransactionTemplateListItem } from '@/types'

export interface TemplateListProps {
  ledgerId: string
  onEdit?: (templateId: string) => void
  /** Called after a template is successfully applied */
  onApplySuccess?: () => void
}

export function TemplateList({ ledgerId, onEdit, onApplySuccess }: TemplateListProps) {
  const { t } = useTranslation()
  const { data: templatesData, isLoading, error } = useTemplates(ledgerId)
  const deleteTemplate = useDeleteTemplate(ledgerId)
  const applyTemplate = useApplyTemplate(ledgerId)

  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [confirmApply, setConfirmApply] = useState<string | null>(null)
  const [applyingId, setApplyingId] = useState<string | null>(null)

  const templates = templatesData?.data || []

  const handleApplyClick = (templateId: string) => {
    setConfirmApply(templateId)
  }

  const handleApplyConfirm = async () => {
    if (!confirmApply) return

    setApplyingId(confirmApply)
    try {
      await applyTemplate.mutateAsync({ templateId: confirmApply })
      onApplySuccess?.()
    } finally {
      setApplyingId(null)
      setConfirmApply(null)
    }
  }

  const handleApplyCancel = () => {
    setConfirmApply(null)
  }

  const handleDeleteClick = (templateId: string) => {
    setConfirmDelete(templateId)
  }

  const handleDeleteConfirm = async () => {
    if (!confirmDelete) return

    await deleteTemplate.mutateAsync(confirmDelete)
    setConfirmDelete(null)
  }

  const handleDeleteCancel = () => {
    setConfirmDelete(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        {t('common.loading')}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-8 text-destructive">
        {t('common.error')}
      </div>
    )
  }

  if (templates.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        {t('templates.noTemplates')}
      </div>
    )
  }

  const templateToDelete = templates.find((t) => t.id === confirmDelete)
  const templateToApply = templates.find((t) => t.id === confirmApply)

  return (
    <div className="space-y-4" data-testid="template-list">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onApply={handleApplyClick}
            onEdit={onEdit}
            onDelete={handleDeleteClick}
            isApplying={applyingId === template.id}
          />
        ))}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!confirmDelete} onOpenChange={() => setConfirmDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('templates.confirmDelete')}</DialogTitle>
            <DialogDescription>
              {templateToDelete && `"${templateToDelete.name}"`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleDeleteCancel} data-testid="cancel-delete">
              {t('common.cancel')}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteTemplate.isPending}
              data-testid="confirm-delete"
            >
              {deleteTemplate.isPending ? t('common.loading') : t('common.delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Apply Confirmation Dialog */}
      <Dialog open={!!confirmApply} onOpenChange={() => setConfirmApply(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('templates.confirmApply')}</DialogTitle>
            <DialogDescription>
              {t('templates.confirmApplyMessage')}
            </DialogDescription>
          </DialogHeader>
          {templateToApply && (
            <div className="rounded-lg border bg-muted/50 p-3 text-sm">
              <div className="mb-1 font-medium">{templateToApply.name}</div>
              <div className="text-muted-foreground">
                ${parseFloat(templateToApply.amount).toFixed(2)} - {templateToApply.description}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={handleApplyCancel} data-testid="cancel-apply">
              {t('common.cancel')}
            </Button>
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
    </div>
  )
}
