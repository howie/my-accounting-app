'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { useCreateTemplate } from '@/lib/hooks/useTemplates'
import type { TransactionType, TransactionTemplateCreate } from '@/types'

export interface SaveTemplateDialogProps {
  ledgerId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Template data from the transaction form */
  templateData: {
    transaction_type: TransactionType
    from_account_id: string
    to_account_id: string
    amount: number
    description: string
  }
  onSuccess?: () => void
}

export function SaveTemplateDialog({
  ledgerId,
  open,
  onOpenChange,
  templateData,
  onSuccess,
}: SaveTemplateDialogProps) {
  const t = useTranslations()
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const createTemplate = useCreateTemplate(ledgerId)

  // Clear form when dialog opens/closes
  useEffect(() => {
    if (open) {
      setName('')
      setError(null)
    }
  }, [open])

  // Clear error when user starts typing
  const handleNameChange = (value: string) => {
    setName(value)
    if (error) {
      setError(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    const trimmedName = name.trim()
    if (!trimmedName) {
      setError(t('validation.templateNameRequired'))
      return
    }

    if (trimmedName.length > 50) {
      setError(t('validation.templateNameTooLong'))
      return
    }

    try {
      const data: TransactionTemplateCreate = {
        name: trimmedName,
        transaction_type: templateData.transaction_type,
        from_account_id: templateData.from_account_id,
        to_account_id: templateData.to_account_id,
        amount: templateData.amount,
        description: templateData.description,
      }

      await createTemplate.mutateAsync(data)
      onOpenChange(false)
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error'))
    }
  }

  const handleCancel = () => {
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('templates.saveTemplate')}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div
              className="rounded bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
              data-testid="template-error"
            >
              {error}
            </div>
          )}

          <div>
            <label htmlFor="template-name" className="mb-2 block text-sm font-medium">
              {t('templates.templateName')}
            </label>
            <Input
              id="template-name"
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder={t('templates.templateNamePlaceholder')}
              maxLength={50}
              autoFocus
              data-testid="template-name-input"
            />
            <div className="mt-1 text-xs text-muted-foreground">{name.length}/50</div>
          </div>

          {/* Show template preview */}
          <div className="rounded-lg border bg-muted/50 p-3 text-sm">
            <div className="mb-1 font-medium">{t('templates.title')}</div>
            <div className="space-y-1 text-muted-foreground">
              <div>
                {t('transactionForm.typeLabel')}: {t(`transactionTypes.${templateData.transaction_type}`)}
              </div>
              <div>
                {t('transactionForm.amountLabel')}: ${templateData.amount.toFixed(2)}
              </div>
              <div>
                {t('transactionForm.descriptionLabel')}: {templateData.description}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              data-testid="cancel-template-button"
            >
              {t('common.cancel')}
            </Button>
            <Button
              type="submit"
              disabled={createTemplate.isPending}
              data-testid="save-template-button"
            >
              {createTemplate.isPending ? t('common.loading') : t('common.save')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
