/**
 * Vocode API Client
 * Handles WebRTC voice call interactions
 */

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
    const response = await axios.get(`${API_URL}/api/vocode/config`)
    return response.data
  },

  /**
   * Start a new voice call
   */
  async startCall(params: {
    system_prompt?: string
    voice?: string
    use_rag?: boolean
  }): Promise<StartCallResponse> {
    const response = await axios.post(`${API_URL}/api/vocode/start`, params)
    return response.data
  },

  /**
   * Get call status
   */
  async getCallStatus(callId: string): Promise<CallStatus> {
    const response = await axios.get(`${API_URL}/api/vocode/status/${callId}`)
    return response.data
  },

  /**
   * End an active call
   */
  async endCall(callId: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_URL}/api/vocode/end/${callId}`)
    return response.data
  },

  /**
   * List all active calls
   */
  async listActiveCalls(): Promise<{ active_calls: ActiveCall[]; count: number }> {
    const response = await axios.get(`${API_URL}/api/vocode/active`)
    return response.data
  },

  /**
   * Get WebSocket URL for a call
   */
  getWebSocketUrl(callId: string): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = API_URL.replace('http://', '').replace('https://', '')
    return `${wsProtocol}//${wsHost}/api/vocode/ws/${callId}`
  },
}
