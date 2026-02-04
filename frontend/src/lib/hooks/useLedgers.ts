

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api'
import type { Ledger, LedgerCreate, LedgerUpdate } from '@/types'

const LEDGERS_KEY = ['ledgers']

interface LedgerListResponse {
  data: Ledger[]
}

export function useLedgers() {
  return useQuery({
    queryKey: LEDGERS_KEY,
    queryFn: async () => {
      const response = await apiGet<LedgerListResponse>('/ledgers')
      return response.data
    },
  })
}

export function useLedger(id: string) {
  return useQuery({
    queryKey: [...LEDGERS_KEY, id],
    queryFn: async () => {
      return apiGet<Ledger>(`/ledgers/${id}`)
    },
    enabled: !!id,
  })
}

export function useCreateLedger() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: LedgerCreate) => {
      return apiPost<Ledger>('/ledgers', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LEDGERS_KEY })
    },
  })
}

export function useUpdateLedger() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: LedgerUpdate }) => {
      return apiPatch<Ledger>(`/ledgers/${id}`, data)
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: LEDGERS_KEY })
      queryClient.invalidateQueries({ queryKey: [...LEDGERS_KEY, id] })
    },
  })
}

export function useDeleteLedger() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      return apiDelete(`/ledgers/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LEDGERS_KEY })
    },
  })
}
