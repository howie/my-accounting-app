

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'
import type {
  Transaction,
  TransactionTemplate,
  TransactionTemplateCreate,
  TransactionTemplateUpdate,
  TransactionTemplateList,
  ApplyTemplateRequest,
  ReorderTemplatesRequest,
} from '@/types'

const TEMPLATES_KEY = 'templates'
const TRANSACTIONS_KEY = 'transactions'

/**
 * Hook to fetch all templates for a ledger
 */
export function useTemplates(ledgerId: string) {
  return useQuery({
    queryKey: [TEMPLATES_KEY, ledgerId],
    queryFn: async () => {
      return apiGet<TransactionTemplateList>(`/ledgers/${ledgerId}/templates`)
    },
    enabled: !!ledgerId,
  })
}

/**
 * Hook to fetch a single template
 */
export function useTemplate(ledgerId: string, templateId: string) {
  return useQuery({
    queryKey: [TEMPLATES_KEY, ledgerId, templateId],
    queryFn: async () => {
      return apiGet<TransactionTemplate>(`/ledgers/${ledgerId}/templates/${templateId}`)
    },
    enabled: !!ledgerId && !!templateId,
  })
}

/**
 * Hook to create a new template
 */
export function useCreateTemplate(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: TransactionTemplateCreate) => {
      return apiPost<TransactionTemplate>(`/ledgers/${ledgerId}/templates`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEMPLATES_KEY, ledgerId] })
    },
  })
}

/**
 * Hook to update an existing template
 */
export function useUpdateTemplate(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      templateId,
      data,
    }: {
      templateId: string
      data: TransactionTemplateUpdate
    }) => {
      return apiPatch<TransactionTemplate>(
        `/ledgers/${ledgerId}/templates/${templateId}`,
        data
      )
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [TEMPLATES_KEY, ledgerId] })
      queryClient.invalidateQueries({
        queryKey: [TEMPLATES_KEY, ledgerId, variables.templateId],
      })
    },
  })
}

/**
 * Hook to delete a template
 */
export function useDeleteTemplate(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (templateId: string) => {
      return apiDelete(`/ledgers/${ledgerId}/templates/${templateId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEMPLATES_KEY, ledgerId] })
    },
  })
}

/**
 * Hook to reorder templates
 */
export function useReorderTemplates(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ReorderTemplatesRequest) => {
      return apiPatch<TransactionTemplateList>(
        `/ledgers/${ledgerId}/templates/reorder`,
        data
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEMPLATES_KEY, ledgerId] })
    },
  })
}

/**
 * Hook to apply a template (create transaction from template)
 */
export function useApplyTemplate(ledgerId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      templateId,
      data,
    }: {
      templateId: string
      data?: ApplyTemplateRequest
    }) => {
      return apiPost<Transaction>(
        `/ledgers/${ledgerId}/templates/${templateId}/apply`,
        data || {}
      )
    },
    onSuccess: () => {
      // Invalidate transactions and accounts (balances changed)
      queryClient.invalidateQueries({ queryKey: [TRANSACTIONS_KEY, ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['accounts', ledgerId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', ledgerId] })
    },
  })
}
