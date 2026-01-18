'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { recurringService } from '@/services/recurring'
import type { RecurringTransactionCreate, RecurringTransactionUpdate } from '@/services/recurring'

const RECURRING_KEY = ['recurring']
const RECURRING_DUE_KEY = ['recurring', 'due']

export function useRecurringTransactions() {
  return useQuery({
    queryKey: RECURRING_KEY,
    queryFn: recurringService.list,
  })
}

export function useDueRecurringTransactions(checkDate?: string) {
  return useQuery({
    queryKey: [...RECURRING_DUE_KEY, { checkDate }],
    queryFn: () => recurringService.getDue(checkDate),
  })
}

export function useCreateRecurringTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RecurringTransactionCreate) => recurringService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RECURRING_KEY })
      queryClient.invalidateQueries({ queryKey: RECURRING_DUE_KEY })
    },
  })
}

export function useUpdateRecurringTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RecurringTransactionUpdate }) =>
      recurringService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RECURRING_KEY })
      queryClient.invalidateQueries({ queryKey: RECURRING_DUE_KEY })
    },
  })
}

export function useDeleteRecurringTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => recurringService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RECURRING_KEY })
      queryClient.invalidateQueries({ queryKey: RECURRING_DUE_KEY })
    },
  })
}

export function useApproveRecurringTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, date }: { id: string; date: string }) => recurringService.approve(id, date),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: RECURRING_DUE_KEY })
      // Also invalidate transactions/accounts if needed, but that's handled by their own hooks usually
      // or we can global invalidate
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}
