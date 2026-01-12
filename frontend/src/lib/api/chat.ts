/**
 * API client for chat functionality.
 */

import { apiPost } from '../api'

export interface ChatRequest {
  message: string
  ledger_id?: string
}

export interface ToolCallResult {
  tool_name: string
  result: Record<string, unknown>
}

export interface ChatResponse {
  id: string
  message: string
  tool_calls: ToolCallResult[]
  created_at: string
}

export const chatApi = {
  /**
   * Send a message to the AI assistant.
   */
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    return apiPost<ChatResponse, ChatRequest>('/chat/messages', request)
  },
}
