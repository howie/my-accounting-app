'use client'

import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import type { AccountTransactionsResponse, TransactionListItem } from '@/types/dashboard'

interface UseAccountTransactionsOptions {
  accountId: string | undefined
  page?: number
  pageSize?: number
}

interface AccountTransactionsData {
  accountId: string
  accountName: string
  transactions: TransactionListItem[]
  totalCount: number
  page: number
  pageSize: number
  hasMore: boolean
}

/**
 * Hook to fetch transactions for a specific account with pagination.
 */
export function useAccountTransactions({
  accountId,
  page = 1,
  pageSize = 50,
}: UseAccountTransactionsOptions) {
  return useQuery<AccountTransactionsData>({
    queryKey: ['account-transactions', accountId, page, pageSize],
    queryFn: async () => {
      if (!accountId) {
        throw new Error('No account selected')
      }
      const response = await apiGet<AccountTransactionsResponse>(
        `/accounts/${accountId}/transactions?page=${page}&page_size=${pageSize}`
      )
      return transformResponse(response)
    },
    enabled: !!accountId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  })
}

/**
 * Transform API response to frontend model.
 */
function transformResponse(response: AccountTransactionsResponse): AccountTransactionsData {
  return {
    accountId: response.account_id,
    accountName: response.account_name,
    transactions: response.transactions.map((t) => ({
      id: t.id,
      date: t.date,
      description: t.description,
      amount: t.amount,
      type: t.type,
      otherAccountName: t.other_account_name,
    })),
    totalCount: response.total_count,
    page: response.page,
    pageSize: response.page_size,
    hasMore: response.has_more,
  }
}
