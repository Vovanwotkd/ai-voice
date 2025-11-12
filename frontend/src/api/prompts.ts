/**
 * Prompts API client
 */

import apiClient from './client'
import type { Prompt, PromptUpdate, PromptVariables } from '@/types'

export const promptsApi = {
  /**
   * Get all prompts
   */
  async getAllPrompts(): Promise<Prompt[]> {
    const { data } = await apiClient.get<Prompt[]>('/prompts/')
    return data
  },

  /**
   * Get active system prompt
   */
  async getActivePrompt(): Promise<Prompt> {
    const { data } = await apiClient.get<Prompt>('/prompts/active')
    return data
  },

  /**
   * Get prompt by ID
   */
  async getPromptById(promptId: string): Promise<Prompt> {
    const { data } = await apiClient.get<Prompt>(`/prompts/${promptId}`)
    return data
  },

  /**
   * Update prompt
   */
  async updatePrompt(promptId: string, update: PromptUpdate): Promise<Prompt> {
    const { data } = await apiClient.put<Prompt>(`/prompts/${promptId}`, update)
    return data
  },

  /**
   * Hot reload prompts
   */
  async reloadPrompts(): Promise<{ status: string; active_prompt: Prompt }> {
    const { data } = await apiClient.post<{ status: string; active_prompt: Prompt }>(
      '/prompts/reload'
    )
    return data
  },

  /**
   * Get available template variables
   */
  async getAvailableVariables(): Promise<PromptVariables> {
    const { data } = await apiClient.get<{ variables: PromptVariables }>(
      '/prompts/variables/available'
    )
    return data.variables
  },

  /**
   * Preview prompt with variable substitution
   */
  async previewPrompt(content: string): Promise<string> {
    const { data } = await apiClient.post<{ preview: string }>('/prompts/preview', {
      content,
    })
    return data.preview
  },
}

export default promptsApi
