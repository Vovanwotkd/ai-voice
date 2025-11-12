/**
 * Chat API client
 */

import apiClient from './client'
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationWithMessages,
} from '@/types'

export const chatApi = {
  /**
   * Send message to the bot
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await apiClient.post<ChatResponse>('/chat/message', request)
    return data
  },

  /**
   * Get all conversations
   */
  async getHistory(limit = 50, offset = 0): Promise<Conversation[]> {
    const { data } = await apiClient.get<Conversation[]>('/chat/history', {
      params: { limit, offset },
    })
    return data
  },

  /**
   * Get specific conversation with messages
   */
  async getConversation(conversationId: string): Promise<ConversationWithMessages> {
    const { data } = await apiClient.get<ConversationWithMessages>(
      `/chat/conversation/${conversationId}`
    )
    return data
  },

  /**
   * Delete conversation
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversation/${conversationId}`)
  },
}

export default chatApi
