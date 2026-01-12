/**
 * React Query hooks for API token management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tokensApi } from '../api/tokens'
import type { ApiTokenCreate } from '@/types'

const TOKENS_KEY = ['tokens']

/**
 * Query hook for fetching all API tokens.
 */
export function useTokens() {
  return useQuery({
    queryKey: TOKENS_KEY,
    queryFn: async () => {
      const response = await tokensApi.list()
      return response.data
    },
  })
}

/**
 * Mutation hook for creating a new API token.
 */
export function useCreateToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ApiTokenCreate) => {
      return tokensApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TOKENS_KEY })
    },
  })
}

/**
 * Mutation hook for revoking an API token.
 */
export function useRevokeToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (tokenId: string) => {
      return tokensApi.revoke(tokenId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TOKENS_KEY })
    },
  })
}
