

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2, Check, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { RecurringForm } from './RecurringForm'
import { useRecurringTransactions, useDeleteRecurringTransaction } from '@/lib/hooks/useRecurring'
import { formatAmount } from '@/lib/utils'
import type { RecurringTransaction } from '@/services/recurring'

export function RecurringList() {
  const { t } = useTranslation(undefined, { keyPrefix: 'recurring' })
  const { data: items, isLoading } = useRecurringTransactions()
  const deleteMutation = useDeleteRecurringTransaction()

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<RecurringTransaction | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id)
      setDeletingId(null)
    } catch (err) {
      console.error('Failed to delete recurring transaction:', err)
    }
  }

  if (isLoading) {
    return <div className="p-4 text-center text-muted-foreground">{t('common.loading')}</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t('title')}</h2>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t('new')}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{t('new')}</DialogTitle>
            </DialogHeader>
            <RecurringForm
              onSuccess={() => setIsCreateOpen(false)}
              onCancel={() => setIsCreateOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border">
        {(!items || items.length === 0) ? (
          <div className="p-8 text-center text-muted-foreground">{t('noData')}</div>
        ) : (
          <div className="divide-y">
            <div className="flex items-center bg-muted/50 px-4 py-3 text-sm font-medium">
              <div className="flex-1">{t('table.name')}</div>
              <div className="w-32">{t('table.frequency')}</div>
              <div className="w-32 text-right">{t('table.amount')}</div>
              <div className="w-32 text-right">{t('table.actions')}</div>
            </div>
            {items.map((item) => (
              <div key={item.id} className="flex items-center px-4 py-3">
                <div className="flex flex-1 items-center gap-3">
                  <span className="font-medium">{item.name}</span>
                </div>
                <div className="w-32 text-sm text-muted-foreground">
                  {t(`frequencies.${item.frequency}`)}
                </div>
                <div className="w-32 text-right font-mono">
                  {formatAmount(item.amount.toString())}
                </div>
                <div className="flex w-32 justify-end gap-2">
                  {deletingId === item.id ? (
                    <>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="h-8 w-8 p-0"
                        onClick={() => handleDelete(item.id)}
                        disabled={deleteMutation.isPending}
                        title={t('common.confirm')}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-8 p-0"
                        onClick={() => setDeletingId(null)}
                        title={t('common.cancel')}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => setEditingItem(item)}
                        title={t('common.edit')} // Using common.edit instead of templates.edit if available
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => setDeletingId(item.id)}
                        title={t('common.delete')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!editingItem} onOpenChange={(open) => !open && setEditingItem(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('table.actions')}</DialogTitle>
          </DialogHeader>
          <RecurringForm
            initialData={editingItem || undefined}
            onSuccess={() => setEditingItem(null)}
            onCancel={() => setEditingItem(null)}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
