

import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import type { TransactionTemplateListItem } from '@/types'

export interface TemplateCardProps {
  template: TransactionTemplateListItem
  onApply: (templateId: string) => void
  onEdit?: (templateId: string) => void
  onDelete?: (templateId: string) => void
  isApplying?: boolean
}

export function TemplateCard({
  template,
  onApply,
  onEdit,
  onDelete,
  isApplying,
}: TemplateCardProps) {
  const { t } = useTranslation()

  const transactionTypeColor = {
    EXPENSE: 'text-red-600 dark:text-red-400',
    INCOME: 'text-green-600 dark:text-green-400',
    TRANSFER: 'text-blue-600 dark:text-blue-400',
  }

  return (
    <div
      className="group rounded-lg border bg-card p-4 transition-colors hover:border-primary/50"
      data-testid={`template-card-${template.id}`}
    >
      <div className="mb-2 flex items-start justify-between">
        <div>
          <h3 className="font-medium" data-testid="template-name">
            {template.name}
          </h3>
          <span
            className={`text-xs ${transactionTypeColor[template.transaction_type]}`}
            data-testid="template-type"
          >
            {t(`transactionTypes.${template.transaction_type}`)}
          </span>
        </div>
        <div
          className="text-lg font-semibold tabular-nums"
          data-testid="template-amount"
        >
          ${parseFloat(template.amount).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </div>
      </div>

      <p
        className="mb-3 text-sm text-muted-foreground line-clamp-2"
        data-testid="template-description"
      >
        {template.description}
      </p>

      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => onApply(template.id)}
          disabled={isApplying}
          data-testid="apply-template-button"
        >
          {isApplying ? t('common.loading') : t('templates.apply')}
        </Button>
        {onEdit && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEdit(template.id)}
            data-testid="edit-template-button"
          >
            {t('templates.edit')}
          </Button>
        )}
        {onDelete && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDelete(template.id)}
            className="text-destructive hover:bg-destructive/10 hover:text-destructive"
            data-testid="delete-template-button"
          >
            {t('templates.delete')}
          </Button>
        )}
      </div>
    </div>
  )
}
