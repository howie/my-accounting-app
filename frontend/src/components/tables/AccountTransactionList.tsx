'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { ArrowRight, ChevronLeft, ChevronRight, Inbox } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAccountTransactions } from '@/lib/hooks/useAccountTransactions'
import { formatAmount } from '@/lib/utils'
import type { TransactionType } from '@/types/dashboard'
import { cn } from '@/lib/utils'

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
 * Simpler read-only view with pagination.
 */
export function AccountTransactionList({ accountId, accountName }: AccountTransactionListProps) {
  const [page, setPage] = useState(1)
  const pageSize = 20
  const t = useTranslations()

  const { data, isLoading, error } = useAccountTransactions({
    accountId,
    page,
    pageSize,
  })

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

  if (transactions.length === 0) {
    return (
      <div className="rounded-lg border p-12 text-center">
        <Inbox className="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
        <h3 className="mb-1 text-lg font-medium text-foreground">
          {t('transactions.noTransactions')}
        </h3>
        <p className="text-sm text-muted-foreground">No transactions found for {displayName}</p>
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
            {totalCount} transaction{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Transaction List */}
      <div className="divide-y rounded-lg border">
        {transactions.map((tx) => (
          <div
            key={tx.id}
            className="flex items-center justify-between p-4 transition-colors hover:bg-muted/50"
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
            <div className={cn('text-right font-mono font-medium', transactionTypeStyles[tx.type])}>
              {transactionTypePrefix[tx.type]}${formatAmount(tx.amount)}
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
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
    </div>
  )
}
