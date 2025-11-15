/**
 * Prompts API client with LocalStorage caching
 */

import apiClient from './client'
import type { Prompt, PromptUpdate, PromptVariables } from '@/types'
import cache from '@/lib/cache'

const PROMPTS_CACHE_KEY = 'prompts'
const PROMPTS_CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export const promptsApi = {
  /**
   * Get all prompts with LocalStorage cache
   */
  async getAllPrompts(): Promise<Prompt[]> {
    // Try cache first for instant loading
    const cached = cache.get<Prompt[]>(PROMPTS_CACHE_KEY, PROMPTS_CACHE_TTL)
    if (cached) {
      console.log('✅ Prompts loaded from cache')
      // Fetch in background to update cache
      apiClient.get<Prompt[]>('/prompts/').then(({ data }) => {
        cache.set(PROMPTS_CACHE_KEY, data)
      }).catch(console.error)
      return cached
    }

    // Fetch from server
    const { data } = await apiClient.get<Prompt[]>('/prompts/')
    cache.set(PROMPTS_CACHE_KEY, data)
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
   * Update prompt and invalidate cache
   */
  async updatePrompt(promptId: string, update: PromptUpdate): Promise<Prompt> {
    const { data } = await apiClient.put<Prompt>(`/prompts/${promptId}`, update)
    // Invalidate cache on update
    cache.remove(PROMPTS_CACHE_KEY)
    return data
  },

  /**
   * Hot reload prompts and clear cache
   */
  async reloadPrompts(): Promise<{ status: string; active_prompt: Prompt }> {
    const { data } = await apiClient.post<{ status: string; active_prompt: Prompt }>(
      '/prompts/reload'
    )
    // Clear cache after reload
    cache.remove(PROMPTS_CACHE_KEY)
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
