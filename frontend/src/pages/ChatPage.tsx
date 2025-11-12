export default function ChatPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">💬 Тестирование бота</h1>
        <p className="text-gray-600 mb-6">
          Здесь будет интерфейс чата для тестирования бота-хостес.
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800 font-medium">🚧 В разработке</p>
          <p className="text-blue-600 text-sm mt-1">
            Chat Interface будет добавлен в следующем коммите.
          </p>
          <p className="text-blue-600 text-sm mt-1">
            Фаза 2 (Часть 1): Базовая структура Frontend готова ✅
          </p>
        </div>

        <div className="mt-6 space-y-2 text-sm text-gray-600">
          <p>✅ React + TypeScript + Vite настроены</p>
          <p>✅ Tailwind CSS подключен</p>
          <p>✅ API клиенты созданы</p>
          <p>✅ Роутинг настроен</p>
          <p>✅ Layout готов</p>
          <p>🔄 Следующий шаг: Chat Interface, Prompt Editor, History</p>
        </div>
      </div>
    </div>
  )
}
