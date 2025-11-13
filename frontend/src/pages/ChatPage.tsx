import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { chatApi } from '@/api/chat'
import type { Message } from '@/types'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      return chatApi.sendMessage({
        message,
        conversation_id: conversationId,
        generate_audio: false,
      })
    },
    onSuccess: (response) => {
      // Add user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        conversation_id: response.conversation_id,
        role: 'user',
        content: input,
        timestamp: new Date().toISOString(),
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        latency_ms: response.latency_ms,
      }

      setMessages((prev) => [...prev, userMessage, assistantMessage])
      setConversationId(response.conversation_id)
      setInput('')
    },
    onError: (error) => {
      console.error('Failed to send message:', error)
      alert('Ошибка при отправке сообщения')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sendMessageMutation.isPending) return
    sendMessageMutation.mutate(input)
  }

  const handleNewConversation = () => {
    setMessages([])
    setConversationId(null)
    setInput('')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">💬 Тестирование бота</h1>
          <p className="text-sm text-gray-500 mt-1">
            {conversationId
              ? `ID разговора: ${conversationId.slice(0, 8)}...`
              : 'Начните новый разговор'}
          </p>
        </div>
        <button
          onClick={handleNewConversation}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
        >
          🔄 Новый разговор
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-xl font-semibold text-gray-700 mb-2">
                Привет! Я бот-хостес ресторана
              </h2>
              <p className="text-gray-500">
                Задайте вопрос или начните разговор о бронировании столика
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-white border-t px-6 py-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите сообщение..."
              disabled={sendMessageMutation.isPending}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={!input.trim() || sendMessageMutation.isPending}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {sendMessageMutation.isPending ? '⏳' : '📤'} Отправить
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
        <div className="flex items-start gap-2">
          <span className="text-lg">{isUser ? '👤' : '🤖'}</span>
          <div className="flex-1">
            <p className="whitespace-pre-wrap">{message.content}</p>
            <div
              className={`text-xs mt-2 ${
                isUser ? 'text-blue-100' : 'text-gray-400'
              }`}
            >
              {new Date(message.timestamp).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit',
              })}
              {message.latency_ms && (
                <span className="ml-2">• {message.latency_ms}ms</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
