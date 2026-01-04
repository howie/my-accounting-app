'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api'
import type { Account, AccountCreate, AccountType, AccountUpdate, AccountTreeNode } from '@/types'

const ACCOUNTS_KEY = (ledgerId: string) => ['ledgers', ledgerId, 'accounts']
const ACCOUNTS_TREE_KEY = (ledgerId: string) => ['ledgers', ledgerId, 'accounts', 'tree']

interface AccountListResponse {
  data: Account[]
}

interface AccountTreeResponse {
  data: AccountTreeNode[]
}

export function useAccounts(ledgerId: string, typeFilter?: AccountType) {
  return useQuery({
    queryKey: [...ACCOUNTS_KEY(ledgerId), { type: typeFilter }],
    queryFn: async () => {
      const params = typeFilter ? `?type=${typeFilter}` : ''
      const response = await apiGet<AccountListResponse>(
        `/ledgers/${ledgerId}/accounts${params}`
      )
      return response.data
    },
    enabled: !!ledgerId,
  })
}

export function useAccount(ledgerId: string, accountId: string) {
  return useQuery({
    queryKey: [...ACCOUNTS_KEY(ledgerId), accountId],
    queryFn: async () => {
      return apiGet<Account>(`/ledgers/${ledgerId}/accounts/${accountId}`)
    },
    enabled: !!ledgerId && !!accountId,
  })
}

export function useCreateAccount(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: AccountCreate) => {
      return apiPost<Account>(`/ledgers/${ledgerId}/accounts`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY(ledgerId) })
    },
  })
}

export function useUpdateAccount(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: AccountUpdate }) => {
      return apiPatch<Account>(`/ledgers/${ledgerId}/accounts/${id}`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY(ledgerId) })
    },
  })
}

export function useDeleteAccount(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      return apiDelete(`/ledgers/${ledgerId}/accounts/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY(ledgerId) })
      queryClient.invalidateQueries({ queryKey: ACCOUNTS_TREE_KEY(ledgerId) })
    },
  })
}

export function useAccountTree(ledgerId: string, typeFilter?: AccountType) {
  return useQuery({
    queryKey: [...ACCOUNTS_TREE_KEY(ledgerId), { type: typeFilter }],
    queryFn: async () => {
      const params = typeFilter ? `?type=${typeFilter}` : ''
      const response = await apiGet<AccountTreeResponse>(
        `/ledgers/${ledgerId}/accounts/tree${params}`
      )
      return response.data
    },
    enabled: !!ledgerId,
  })
}
