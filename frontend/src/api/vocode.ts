/**
 * Vocode API Client
 * Handles WebRTC voice call interactions
 */

import apiClient from './client'

export interface VocodeConfig {
  voices: Record<string, string>
  system_prompts: Record<string, string>
  audio_config: {
    sample_rate: number
    encoding: string
    channels: number
  }
}

export interface StartCallResponse {
  call_id: string
  status: string
  websocket_url: string
  message: string
}

export interface CallStatus {
  call_id: string
  status: 'active' | 'ended' | 'error'
  duration_seconds?: number
}

export interface ActiveCall {
  call_id: string
  status: string
}

export const vocodeApi = {
  /**
   * Get Vocode configuration (voices, prompts, audio settings)
   */
  async getConfig(): Promise<VocodeConfig> {
    const { data } = await apiClient.get('/vocode/config')
    return data
  },

  /**
   * Start a new voice call
   */
  async startCall(params: {
    system_prompt?: string
    voice?: string
    use_rag?: boolean
  }): Promise<StartCallResponse> {
    const { data } = await apiClient.post('/vocode/start', params)
    return data
  },

  /**
   * Get call status
   */
  async getCallStatus(callId: string): Promise<CallStatus> {
    const { data } = await apiClient.get(`/vocode/status/${callId}`)
    return data
  },

  /**
   * End an active call
   */
  async endCall(callId: string): Promise<{ message: string }> {
    const { data } = await apiClient.post(`/vocode/end/${callId}`)
    return data
  },

  /**
   * List all active calls
   */
  async listActiveCalls(): Promise<{ active_calls: ActiveCall[]; count: number }> {
    const { data } = await apiClient.get('/vocode/active')
    return data
  },

  /**
   * Get WebSocket URL for a call
   */
  getWebSocketUrl(callId: string): string {
    // Construct WebSocket URL based on current window location
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    return `${wsProtocol}//${wsHost}/api/vocode/ws/${callId}`
  },
}
