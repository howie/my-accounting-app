/**
 * API client for token management.
 */

import { apiGet, apiPost, apiDelete } from '../api'
import type { ApiToken, ApiTokenCreate, ApiTokenCreateResponse, ApiTokenList } from '@/types'

export const tokensApi = {
  /**
   * List all API tokens for the current user.
   */
  list: async (): Promise<ApiTokenList> => {
    return apiGet<ApiTokenList>('/tokens')
  },

  /**
   * Create a new API token.
   * Returns the full token value only once - must be stored by client.
   */
  create: async (data: ApiTokenCreate): Promise<ApiTokenCreateResponse> => {
    return apiPost<ApiTokenCreateResponse, ApiTokenCreate>('/tokens', data)
  },

  /**
   * Revoke an API token by ID.
   */
  revoke: async (tokenId: string): Promise<void> => {
    return apiDelete(`/tokens/${tokenId}`)
  },
}
