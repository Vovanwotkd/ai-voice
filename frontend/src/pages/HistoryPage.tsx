import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { chatApi } from '@/api/chat'
import type { Conversation, Message } from '@/types'

export default function HistoryPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [limit] = useState(50)
  const [offset] = useState(0)

  // Load conversations
  const { data: conversations, isLoading, error } = useQuery({
    queryKey: ['conversations', limit, offset],
    queryFn: () => chatApi.getHistory(limit, offset),
  })

  // Ensure conversations is an array
  const conversationsArray = Array.isArray(conversations) ? conversations : []

  // Load selected conversation details
  const { data: conversationDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['conversation', selectedConversationId],
    queryFn: () =>
      selectedConversationId ? chatApi.getConversation(selectedConversationId) : null,
    enabled: !!selectedConversationId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <p className="text-gray-600">Загрузка истории...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">❌</div>
          <p className="text-gray-600">Ошибка загрузки истории</p>
          <p className="text-sm text-gray-500 mt-2">{String(error)}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Conversations list */}
      <div className="w-96 bg-white border-r overflow-y-auto">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="text-xl font-bold">📜 История разговоров</h2>
          <p className="text-sm text-gray-500 mt-1">
            Всего: {conversationsArray.length} разговоров
          </p>
        </div>

        <div className="divide-y">
          {conversationsArray.length > 0 ? (
            conversationsArray.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isSelected={selectedConversationId === conversation.id}
                onClick={() => setSelectedConversationId(conversation.id)}
              />
            ))
          ) : (
            <div className="p-8 text-center">
              <div className="text-4xl mb-2">📭</div>
              <p className="text-gray-500">Пока нет разговоров</p>
              <p className="text-sm text-gray-400 mt-1">
                Начните новый разговор в разделе "Тестирование"
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Conversation details */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {selectedConversationId ? (
          detailsLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-4xl mb-2">⏳</div>
                <p className="text-gray-600">Загрузка сообщений...</p>
              </div>
            </div>
          ) : conversationDetails ? (
            <>
              {/* Header */}
              <div className="bg-white border-b px-6 py-4">
                <h3 className="text-lg font-bold">Разговор {conversationDetails.id.slice(0, 8)}...</h3>
                <div className="flex gap-4 text-sm text-gray-500 mt-1">
                  <span>📅 {new Date(conversationDetails.created_at).toLocaleString('ru-RU')}</span>
                  <span>💬 {conversationDetails.messages?.length || 0} сообщений</span>
                  {conversationDetails.metadata && (
                    <span>🏷️ {JSON.stringify(conversationDetails.metadata)}</span>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-4">
                  {conversationDetails.messages && conversationDetails.messages.length > 0 ? (
                    conversationDetails.messages.map((message) => (
                      <MessageBubble key={message.id} message={message} />
                    ))
                  ) : (
                    <div className="text-center text-gray-500">Нет сообщений</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-4xl mb-2">❌</div>
                <p className="text-gray-600">Не удалось загрузить разговор</p>
              </div>
            </div>
          )
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Выберите разговор
              </h3>
              <p className="text-gray-500">
                Выберите разговор из списка слева для просмотра деталей
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ConversationItem({
  conversation,
  isSelected,
  onClick,
}: {
  conversation: Conversation
  isSelected: boolean
  onClick: () => void
}) {
  const lastMessage = conversation.messages?.[conversation.messages.length - 1]
  const messageCount = conversation.messages?.length || 0

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
        isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="font-medium text-sm">
          ID: {conversation.id.slice(0, 8)}...
        </span>
        <span className="text-xs text-gray-400">
          {new Date(conversation.created_at).toLocaleDateString('ru-RU')}
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
        <span>💬 {messageCount} сообщений</span>
        <span>•</span>
        <span>
          {new Date(conversation.created_at).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      {lastMessage && (
        <p className="text-sm text-gray-600 line-clamp-2">
          {lastMessage.role === 'user' ? '👤 ' : '🤖 '}
          {lastMessage.content}
        </p>
      )}

      {conversation.metadata && Object.keys(conversation.metadata).length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {Object.entries(conversation.metadata).map(([key, value]) => (
            <span
              key={key}
              className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600"
            >
              {key}: {String(value)}
            </span>
          ))}
        </div>
      )}
    </button>
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
                second: '2-digit',
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
