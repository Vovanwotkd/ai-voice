import { useQuery } from '@tanstack/react-query'
import { chatApi } from '@/api/chat'

export default function DashboardPage() {
  // Load conversations for statistics
  const { data: conversations, isLoading, error } = useQuery({
    queryKey: ['dashboard-conversations'],
    queryFn: () => chatApi.getHistory(1000, 0), // Get up to 1000 conversations for stats
  })

  // Ensure conversations is an array
  const conversationsArray = Array.isArray(conversations) ? conversations : []

  // Calculate statistics
  const stats = {
    totalConversations: conversationsArray.length,
    totalMessages:
      conversationsArray.reduce((sum, conv) => sum + (conv.messages?.length || 0), 0),
    averageLatency: 0,
    recentConversations: 0,
  }

  // Calculate average latency from all assistant messages
  if (conversationsArray.length > 0) {
    const latencies: number[] = []
    conversationsArray.forEach((conv) => {
      conv.messages?.forEach((msg) => {
        if (msg.role === 'assistant' && msg.latency_ms) {
          latencies.push(msg.latency_ms)
        }
      })
    })
    if (latencies.length > 0) {
      stats.averageLatency = Math.round(
        latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length
      )
    }
  }

  // Count conversations in last 24 hours
  if (conversationsArray.length > 0) {
    const oneDayAgo = new Date()
    oneDayAgo.setHours(oneDayAgo.getHours() - 24)
    stats.recentConversations = conversationsArray.filter(
      (conv) => new Date(conv.created_at) > oneDayAgo
    ).length
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <p className="text-gray-600">Загрузка статистики...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">❌</div>
          <p className="text-gray-600">Ошибка загрузки статистики</p>
          <p className="text-sm text-gray-500 mt-2">{String(error)}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">📊 Дашборд</h1>
        <p className="text-gray-600">
          Статистика и метрики работы AI Voice Hostess Bot
        </p>
      </div>

      {/* Main stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon="💬"
          title="Всего разговоров"
          value={stats.totalConversations}
          color="blue"
        />
        <StatCard
          icon="📨"
          title="Всего сообщений"
          value={stats.totalMessages}
          color="green"
        />
        <StatCard
          icon="⚡"
          title="Среднее время ответа"
          value={`${stats.averageLatency} мс`}
          color="purple"
        />
        <StatCard
          icon="🔥"
          title="За последние 24ч"
          value={stats.recentConversations}
          color="orange"
        />
      </div>

      {/* Recent conversations */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">📜 Последние разговоры</h2>
        {conversationsArray.length > 0 ? (
          <div className="space-y-2">
            {conversationsArray.slice(0, 5).map((conversation) => (
              <div
                key={conversation.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm text-gray-600">
                      {conversation.id.slice(0, 8)}...
                    </span>
                    <span className="text-xs text-gray-400">
                      {conversation.messages?.length || 0} сообщений
                    </span>
                  </div>
                  {conversation.messages && conversation.messages.length > 0 && (
                    <p className="text-sm text-gray-600 line-clamp-1">
                      {conversation.messages[0].content}
                    </p>
                  )}
                </div>
                <span className="text-xs text-gray-400 ml-4">
                  {new Date(conversation.created_at).toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📭</div>
            <p>Пока нет разговоров</p>
          </div>
        )}
      </div>

      {/* System info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-3">🤖 Информация о системе</h3>
          <div className="space-y-2 text-sm">
            <InfoRow label="Версия" value="1.0.0" />
            <InfoRow label="Backend API" value={import.meta.env.VITE_API_URL || '/api'} />
            <InfoRow label="Статус" value="🟢 Онлайн" />
            <InfoRow
              label="Последнее обновление"
              value={new Date().toLocaleDateString('ru-RU')}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-3">📈 Статистика использования</h3>
          <div className="space-y-2 text-sm">
            <InfoRow
              label="Среднее сообщений на разговор"
              value={
                stats.totalConversations > 0
                  ? (stats.totalMessages / stats.totalConversations).toFixed(1)
                  : '0'
              }
            />
            <InfoRow
              label="Активность за 24ч"
              value={`${((stats.recentConversations / stats.totalConversations) * 100 || 0).toFixed(1)}%`}
            />
            <InfoRow
              label="Производительность"
              value={stats.averageLatency < 1000 ? '🟢 Отлично' : stats.averageLatency < 3000 ? '🟡 Хорошо' : '🔴 Медленно'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  icon,
  title,
  value,
  color,
}: {
  icon: string
  title: string
  value: string | number
  color: 'blue' | 'green' | 'purple' | 'orange'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
  }

  return (
    <div className={`rounded-lg border p-6 ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <p className="text-sm font-medium">{title}</p>
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-600">{label}:</span>
      <span className="font-medium text-gray-800">{value}</span>
    </div>
  )
}
