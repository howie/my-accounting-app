'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { installmentService } from '@/services/installments'
import type { InstallmentPlanCreate } from '@/services/installments'

const INSTALLMENTS_KEY = ['installments']

export function useInstallmentPlans() {
  return useQuery({
    queryKey: INSTALLMENTS_KEY,
    queryFn: installmentService.list,
  })
}

export function useInstallmentPlan(id: string) {
  return useQuery({
    queryKey: [...INSTALLMENTS_KEY, id],
    queryFn: () => installmentService.get(id),
    enabled: !!id,
  })
}

export function useInstallmentTransactions(id: string) {
  return useQuery({
    queryKey: [...INSTALLMENTS_KEY, id, 'transactions'],
    queryFn: () => installmentService.getTransactions(id),
    enabled: !!id,
  })
}

export function useCreateInstallmentPlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InstallmentPlanCreate) => installmentService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INSTALLMENTS_KEY })
      // Invalidate transactions as they are created immediately
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}
