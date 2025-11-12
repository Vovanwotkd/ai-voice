/**
 * TypeScript type definitions for the application
 */

// Message types
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  audio_url?: string
  latency_ms?: number
}

// Conversation types
export interface Conversation {
  id: string
  session_id?: string
  started_at: string
  ended_at?: string
  message_count: number
  metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[]
}

// Prompt types
export interface Prompt {
  id: string
  name: string
  content: string
  variables?: Record<string, unknown>
  version: number
  is_active: boolean
  description?: string
  created_at: string
  updated_at: string
}

// Chat request/response types
export interface ChatRequest {
  message: string
  conversation_id?: string | null
  generate_audio?: boolean
}

export interface ChatResponse {
  conversation_id: string
  message: string
  audio_url?: string | null
  latency_ms: number
}

// Prompt update types
export interface PromptUpdate {
  content?: string
  is_active?: boolean
  description?: string
}

export interface PromptVariables {
  [key: string]: string
}

// API response types
export interface ApiError {
  detail: string
}

export interface HealthResponse {
  status: string
  service?: string
  version?: string
  checks?: Record<string, string>
}
