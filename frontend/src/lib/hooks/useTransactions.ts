import { useMutation, useQuery, useQueryClient, useInfiniteQuery } from '@tanstack/react-query'

import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api'
import type {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  TransactionListItem,
  PaginatedResponse,
  TransactionType,
} from '@/types'

const TRANSACTIONS_KEY = 'transactions'

export interface TransactionFilters {
  search?: string
  fromDate?: string
  toDate?: string
  accountId?: string
  transactionType?: TransactionType
  tagId?: string
}

export function useTransactions(ledgerId: string, filters?: TransactionFilters) {
  return useInfiniteQuery({
    queryKey: [TRANSACTIONS_KEY, ledgerId, filters],
    queryFn: async ({ pageParam }) => {
      const params = new URLSearchParams()

      if (pageParam) {
        params.set('cursor', pageParam)
      }
      if (filters?.search) {
        params.set('search', filters.search)
      }
      if (filters?.fromDate) {
        params.set('from_date', filters.fromDate)
      }
      if (filters?.toDate) {
        params.set('to_date', filters.toDate)
      }
      if (filters?.accountId) {
        params.set('account_id', filters.accountId)
      }
      if (filters?.transactionType) {
        params.set('transaction_type', filters.transactionType)
      }
      if (filters?.tagId) {
        params.set('tag_id', filters.tagId)
      }

      const queryString = params.toString()
      const url = queryString
        ? `/ledgers/${ledgerId}/transactions?${queryString}`
        : `/ledgers/${ledgerId}/transactions`

      return apiGet<PaginatedResponse<TransactionListItem>>(url)
    },
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.cursor,
  })
}

export function useTransaction(ledgerId: string, transactionId: string) {
  return useQuery({
    queryKey: [TRANSACTIONS_KEY, ledgerId, transactionId],
    queryFn: async () => {
      return apiGet<Transaction>(`/ledgers/${ledgerId}/transactions/${transactionId}`)
    },
    enabled: !!transactionId,
  })
}

export function useCreateTransaction(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: TransactionCreate) => {
      return apiPost<Transaction>(`/ledgers/${ledgerId}/transactions`, data)
    },
    onSuccess: () => {
      // Invalidate transactions and accounts (balances changed)
      queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_KEY, ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['accounts', ledgerId] })
    },
  })
}

export function useUpdateTransaction(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      transactionId,
      data,
    }: {
      transactionId: string
      data: TransactionUpdate
    }) => {
      return apiPut<Transaction>(`/ledgers/${ledgerId}/transactions/${transactionId}`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_KEY, ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['accounts', ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['account-transactions'] })
    },
  })
}

export interface TransactionSuggestion {
  description: string
  count: number
  fromAccountId: string
  toAccountId: string
  type: string
}

export function useTransactionSuggestions(ledgerId: string) {
  return useQuery({
    queryKey: ['transaction-suggestions', ledgerId],
    queryFn: async () => {
      const result = await apiGet<PaginatedResponse<TransactionListItem>>(
        `/ledgers/${ledgerId}/transactions?limit=100`
      )
      const descMap = new Map<
        string,
        { count: number; fromAccountId: string; toAccountId: string; type: string }
      >()
      for (const tx of result.data) {
        const existing = descMap.get(tx.description)
        if (existing) {
          existing.count++
        } else {
          descMap.set(tx.description, {
            count: 1,
            fromAccountId: tx.from_account.id,
            toAccountId: tx.to_account.id,
            type: tx.transaction_type,
          })
        }
      }
      return Array.from(descMap.entries())
        .sort((a, b) => b[1].count - a[1].count)
        .map(([description, meta]) => ({ description, ...meta }))
    },
    enabled: !!ledgerId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useDeleteTransaction(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transactionId: string) => {
      return apiDelete(`/ledgers/${ledgerId}/transactions/${transactionId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_KEY, ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['accounts', ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['account-transactions'] })
    },
  })
}
