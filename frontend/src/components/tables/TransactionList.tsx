

import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import {
  useTransactions,
  useDeleteTransaction,
  type TransactionFilters,
} from '@/lib/hooks/useTransactions'
import { formatAmount } from '@/lib/utils'
import type { TransactionType } from '@/types'

interface TransactionListProps {
  ledgerId: string
  filters?: TransactionFilters
}

const transactionTypeStyles: Record<TransactionType, string> = {
  EXPENSE: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  INCOME: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  TRANSFER: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
}

export function TransactionList({ ledgerId, filters }: TransactionListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, error } =
    useTransactions(ledgerId, filters)
  const deleteTransaction = useDeleteTransaction(ledgerId)
  const { t } = useTranslation()

  const handleDelete = async (id: string) => {
    try {
      await deleteTransaction.mutateAsync(id)
      setDeletingId(null)
    } catch (err) {
      console.error('Failed to delete transaction:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center text-muted-foreground">
        {t('transactions.loadingTransactions')}
      </div>
    )
  }

  if (error) {
    return <div className="text-center text-destructive">{t('transactions.errorLoading')}</div>
  }

  const transactions = data?.pages.flatMap((page) => page.data) || []

  if (transactions.length === 0) {
    return (
      <div className="rounded-lg border p-8 text-center text-muted-foreground">
        {t('transactions.noTransactions')}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">{t('table.date')}</th>
                <th className="px-4 py-3 text-left text-sm font-medium">
                  {t('table.description')}
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium">{t('table.type')}</th>
                <th className="px-4 py-3 text-left text-sm font-medium">{t('table.from')}</th>
                <th className="px-4 py-3 text-left text-sm font-medium">{t('table.to')}</th>
                <th className="px-4 py-3 text-right text-sm font-medium">{t('table.amount')}</th>
                <th className="px-4 py-3 text-right text-sm font-medium">{t('table.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-muted/50">
                  <td className="px-4 py-3 text-sm">{tx.date}</td>
                  <td className="px-4 py-3 text-sm font-medium">
                    <div>{tx.description}</div>
                    {tx.tags && tx.tags.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {tx.tags.map((tag) => (
                          <span
                            key={tag.id}
                            className="inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px]"
                            style={{
                              backgroundColor: tag.color + '20',
                              borderColor: tag.color,
                              color: tag.color,
                            }}
                          >
                            {tag.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded px-2 py-1 text-xs font-medium ${
                        transactionTypeStyles[tx.transaction_type]
                      }`}
                    >
                      {t(`transactionTypes.${tx.transaction_type}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{tx.from_account.name}</td>
                  <td className="px-4 py-3 text-sm">{tx.to_account.name}</td>
                  <td className="px-4 py-3 text-right font-mono text-sm">
                    ${formatAmount(tx.amount)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {deletingId === tx.id ? (
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(tx.id)}
                          disabled={deleteTransaction.isPending}
                        >
                          {t('common.confirm')}
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => setDeletingId(null)}>
                          {t('common.cancel')}
                        </Button>
                      </div>
                    ) : (
                      <Button variant="ghost" size="sm" onClick={() => setDeletingId(tx.id)}>
                        {t('common.delete')}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {hasNextPage && (
        <div className="text-center">
          <Button variant="outline" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? t('common.loading') : t('common.loadMore')}
          </Button>
        </div>
      )}
    </div>
  )
}
