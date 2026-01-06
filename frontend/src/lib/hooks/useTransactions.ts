'use client'

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
    },
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
    },
  })
}
