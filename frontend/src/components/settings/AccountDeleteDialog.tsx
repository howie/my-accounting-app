

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { X, AlertTriangle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  useCanDeleteAccount,
  useReplacementCandidates,
  useDeleteAccount,
  useReassignAndDelete,
} from '@/lib/hooks/useAccounts'
import { cn } from '@/lib/utils'
import type { AccountTreeNode } from '@/types'

interface AccountDeleteDialogProps {
  account: AccountTreeNode | null
  ledgerId: string
  isOpen: boolean
  onClose: () => void
}

export function AccountDeleteDialog({
  account,
  ledgerId,
  isOpen,
  onClose,
}: AccountDeleteDialogProps) {
  const { t } = useTranslation()
  const [selectedReplacementId, setSelectedReplacementId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  // Fetch delete status
  const { data: canDeleteData, isLoading: loadingCanDelete } = useCanDeleteAccount(
    ledgerId,
    account?.id || ''
  )

  // Fetch replacement candidates
  const { data: replacementCandidates, isLoading: loadingCandidates } = useReplacementCandidates(
    ledgerId,
    account?.id || ''
  )

  const deleteAccount = useDeleteAccount(ledgerId)
  const reassignAndDelete = useReassignAndDelete(ledgerId)

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setSelectedReplacementId('')
      setError(null)
    }
  }, [isOpen, account])

  const handleDelete = async () => {
    if (!account) return
    setError(null)

    try {
      if (canDeleteData?.has_transactions && selectedReplacementId) {
        // Reassign transactions and delete
        await reassignAndDelete.mutateAsync({
          accountId: account.id,
          replacementAccountId: selectedReplacementId,
        })
      } else {
        // Direct delete
        await deleteAccount.mutateAsync(account.id)
      }
      onClose()
    } catch (err) {
      setError(t('accountManagement.deleteAccount') + ' failed')
      console.error('Failed to delete account:', err)
    }
  }

  if (!isOpen || !account) return null

  const isLoading = loadingCanDelete || loadingCandidates
  const isPending = deleteAccount.isPending || reassignAndDelete.isPending

  // Check if deletion is blocked
  const hasChildren = canDeleteData?.has_children || false
  const hasTransactions = canDeleteData?.has_transactions || false
  const transactionCount = canDeleteData?.transaction_count || 0
  const childCount = canDeleteData?.child_count || 0

  // Cannot delete if has children
  const cannotDelete = hasChildren || account.is_system

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />

      {/* Dialog */}
      <div className="relative z-10 mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-destructive">
            <AlertTriangle className="h-5 w-5" />
            {t('accountManagement.deleteAccount')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : (
            <>
              {/* Account info */}
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="font-medium">{account.name}</p>
                <p className="text-sm text-muted-foreground">{t(`accountTypes.${account.type}`)}</p>
              </div>

              {/* System account warning */}
              {account.is_system && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4">
                  <p className="text-sm text-destructive">
                    {t('accountManagement.cannotDeleteSystem')}
                  </p>
                </div>
              )}

              {/* Children warning */}
              {hasChildren && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4">
                  <p className="text-sm text-destructive">
                    {t('accountManagement.hasChildren', { count: childCount })}
                  </p>
                  <p className="mt-1 text-sm text-destructive">
                    {t('accountManagement.cannotDeleteChildren')}
                  </p>
                </div>
              )}

              {/* Transaction reassignment */}
              {!cannotDelete && hasTransactions && (
                <div className="space-y-3">
                  <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-4">
                    <p className="text-sm text-amber-700 dark:text-amber-400">
                      {t('accountManagement.hasTransactions', { count: transactionCount })}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="replacement" className="text-sm font-medium">
                      {t('accountManagement.selectReplacement')}
                    </label>
                    <select
                      id="replacement"
                      value={selectedReplacementId}
                      onChange={(e) => setSelectedReplacementId(e.target.value)}
                      className={cn(
                        'h-10 w-full rounded-md border border-input bg-background px-3',
                        'text-sm focus:outline-none focus:ring-2 focus:ring-ring'
                      )}
                    >
                      <option value="">{t('transactionForm.selectAccount')}</option>
                      {replacementCandidates?.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          {candidate.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Simple confirmation */}
              {!cannotDelete && !hasTransactions && (
                <p className="text-sm text-muted-foreground">
                  {t('accountManagement.confirmDelete')}
                </p>
              )}

              {error && <p className="text-sm text-destructive">{error}</p>}
            </>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
              {t('common.cancel')}
            </Button>
            {!cannotDelete && (
              <Button
                type="button"
                variant="destructive"
                onClick={handleDelete}
                disabled={isPending || isLoading || (hasTransactions && !selectedReplacementId)}
              >
                {isPending
                  ? t('common.loading')
                  : hasTransactions
                    ? t('accountManagement.reassignAndDelete')
                    : t('common.delete')}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
