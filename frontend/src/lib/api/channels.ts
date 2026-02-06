/**
 * API client for channel binding management.
 */

import { apiGet, apiPost, apiDelete } from '../api'
import type { ChannelBinding, GenerateCodeRequest, GenerateCodeResponse } from '@/types'

export const channelsApi = {
  /**
   * List all channel bindings for the current user.
   */
  list: async (includeInactive = false): Promise<ChannelBinding[]> => {
    const params = includeInactive ? '?include_inactive=true' : ''
    return apiGet<ChannelBinding[]>(`/channels/bindings${params}`)
  },

  /**
   * Generate a 6-digit verification code for channel binding.
   */
  generateCode: async (data: GenerateCodeRequest): Promise<GenerateCodeResponse> => {
    return apiPost<GenerateCodeResponse, GenerateCodeRequest>(
      '/channels/bindings/generate-code',
      data
    )
  },

  /**
   * Unbind a channel (soft delete).
   */
  unbind: async (bindingId: string): Promise<void> => {
    return apiDelete(`/channels/bindings/${bindingId}`)
  },
}
