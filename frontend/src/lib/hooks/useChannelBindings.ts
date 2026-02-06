/**
 * React Query hooks for channel binding management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { channelsApi } from '../api/channels'
import type { GenerateCodeRequest } from '@/types'

const BINDINGS_KEY = ['channel-bindings']

/**
 * Query hook for fetching all active channel bindings.
 */
export function useChannelBindings() {
  return useQuery({
    queryKey: BINDINGS_KEY,
    queryFn: () => channelsApi.list(),
  })
}

/**
 * Mutation hook for generating a binding verification code.
 */
export function useGenerateCode() {
  return useMutation({
    mutationFn: (data: GenerateCodeRequest) => channelsApi.generateCode(data),
  })
}

/**
 * Mutation hook for unbinding a channel.
 */
export function useUnbindChannel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bindingId: string) => channelsApi.unbind(bindingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BINDINGS_KEY })
    },
  })
}
