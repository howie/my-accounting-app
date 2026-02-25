import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Pencil,
  Search,
  Trash2,
  X,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TransactionModal } from '@/components/transactions/TransactionModal'
import { useAccountTransactions } from '@/lib/hooks/useAccountTransactions'
import { useDeleteTransaction, useTransaction } from '@/lib/hooks/useTransactions'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { formatAmount } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { TransactionType } from '@/types/dashboard'
import type { Transaction } from '@/types'

interface AccountTransactionListProps {
  accountId: string
  accountName?: string
}

const transactionTypeStyles: Record<TransactionType, string> = {
  EXPENSE: 'text-red-500 dark:text-red-400',
  INCOME: 'text-green-500 dark:text-green-400',
  TRANSFER: 'text-blue-500 dark:text-blue-400',
}

const transactionTypePrefix: Record<TransactionType, string> = {
  EXPENSE: '-',
  INCOME: '+',
  TRANSFER: '',
}

/**
 * Transaction list for a single account.
 * Supports search, edit, delete, and running balance display.
 */
export function AccountTransactionList({ accountId, accountName }: AccountTransactionListProps) {
  const [page, setPage] = useState(1)
  const pageSize = 20
  const { t } = useTranslation()
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id ?? ''

  const [searchQuery, setSearchQuery] = useState('')
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [editTargetId, setEditTargetId] = useState<string | null>(null)
  const [editModalOpen, setEditModalOpen] = useState(false)

  const { data, isLoading, error } = useAccountTransactions({
    accountId,
    page,
    pageSize,
  })

  const deleteTransaction = useDeleteTransaction(ledgerId)

  // Fetch full transaction data for edit mode
  const { data: editTransactionData } = useTransaction(ledgerId, editTargetId ?? '')

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTargetId || !ledgerId) return
    await deleteTransaction.mutateAsync(deleteTargetId)
    setDeleteTargetId(null)
  }, [deleteTargetId, ledgerId, deleteTransaction])

  const handleEditClick = useCallback((transactionId: string) => {
    setEditTargetId(transactionId)
    setEditModalOpen(true)
  }, [])

  const handleEditModalClose = useCallback((open: boolean) => {
    setEditModalOpen(open)
    if (!open) {
      setEditTargetId(null)
    }
  }, [])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 animate-pulse rounded bg-muted" />
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 animate-pulse rounded bg-muted/50" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950">
        <p className="text-red-600 dark:text-red-400">{t('transactions.errorLoading')}</p>
        <p className="mt-1 text-sm text-red-500">{error.message}</p>
      </div>
    )
  }

  const transactions = data?.transactions ?? []
  const displayName = accountName ?? data?.accountName ?? 'Account'
  const totalCount = data?.totalCount ?? 0
  const hasMore = data?.hasMore ?? false
  const totalPages = Math.ceil(totalCount / pageSize)

  // Client-side search filtering
  const filteredTransactions = searchQuery
    ? transactions.filter(
        (tx) =>
          tx.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tx.otherAccountName.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : transactions

  if (transactions.length === 0) {
    return (
      <div className="rounded-lg border p-12 text-center">
        <Inbox className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
        <h3 className="mb-1 text-lg font-medium text-foreground">
          {t('transactions.noTransactions')}
        </h3>
        <p className="text-sm text-muted-foreground">
          {t('accountPage.noTransactionsFor', { name: displayName })}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">{displayName}</h2>
          <p className="text-sm text-muted-foreground">
            {t('accountPage.transactionCount', { count: totalCount })}
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('transactions.searchPlaceholder')}
          className="pl-9 pr-9"
          data-testid="search-transactions"
        />
        {searchQuery && (
          <button
            type="button"
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Search result count */}
      {searchQuery && (
        <p className="text-sm text-muted-foreground">
          {filteredTransactions.length > 0
            ? t('transactions.searchResults', { count: filteredTransactions.length })
            : t('transactions.noSearchResults')}
        </p>
      )}

      {/* Transaction List */}
      {filteredTransactions.length > 0 && (
        <div className="divide-y rounded-lg border">
          {filteredTransactions.map((tx) => (
            <div
              key={tx.id}
              className="group flex items-center justify-between p-4 transition-colors hover:bg-muted/50"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium">{tx.description}</span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{tx.date}</span>
                  <ArrowRight className="h-3 w-3" />
                  <span className="truncate">{tx.otherAccountName}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* Amount */}
                <div
                  className={cn('text-right font-mono font-medium', transactionTypeStyles[tx.type])}
                >
                  {transactionTypePrefix[tx.type]}
                  {formatAmount(tx.amount)}
                </div>

                {/* Action buttons - show on hover */}
                <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    type="button"
                    onClick={() => handleEditClick(tx.id)}
                    className="rounded p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
                    title={t('transactions.edit')}
                    data-testid={`edit-transaction-${tx.id}`}
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteTargetId(tx.id)}
                    className="rounded p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    title={t('transactions.deleteTransaction')}
                    data-testid={`delete-transaction-${tx.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !searchQuery && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {t('accountPage.pageInfo', { page, total: totalPages })}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              {t('common.previous')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
            >
              {t('common.next')}
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTargetId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          data-testid="delete-transaction-dialog"
        >
          <div
            className="absolute inset-0 bg-black/50"
            aria-hidden="true"
            onClick={() => setDeleteTargetId(null)}
          />
          <div className="relative z-10 mx-4 w-full max-w-sm rounded-lg border bg-background p-6 shadow-lg">
            <h3 id="delete-dialog-title" className="mb-2 text-lg font-semibold">
              {t('transactions.deleteTransaction')}
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">{t('transactions.deleteConfirm')}</p>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setDeleteTargetId(null)}
                disabled={deleteTransaction.isPending}
              >
                {t('common.cancel')}
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={handleDeleteConfirm}
                disabled={deleteTransaction.isPending}
                data-testid="confirm-delete-button"
              >
                {deleteTransaction.isPending ? t('common.loading') : t('common.delete')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal */}
      {ledgerId && (
        <TransactionModal
          ledgerId={ledgerId}
          editTransaction={editTransactionData as Transaction | undefined}
          open={editModalOpen && !!editTransactionData}
          onOpenChange={handleEditModalClose}
          onTransactionCreated={() => {
            setEditTargetId(null)
            setEditModalOpen(false)
          }}
        />
      )}
    </div>
  )
}
