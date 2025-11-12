export default function DashboardPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">📊 Дашборд</h1>
        <p className="text-gray-600 mb-6">
          Здесь будет статистика и метрики работы бота.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-blue-600 text-sm font-medium">Всего разговоров</p>
            <p className="text-2xl font-bold text-blue-900 mt-2">0</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-green-600 text-sm font-medium">Среднее время ответа</p>
            <p className="text-2xl font-bold text-green-900 mt-2">0 мс</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <p className="text-purple-600 text-sm font-medium">Активных сессий</p>
            <p className="text-2xl font-bold text-purple-900 mt-2">0</p>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-gray-800 font-medium">🚧 В разработке</p>
          <p className="text-gray-600 text-sm mt-1">
            Dashboard с реальными метриками будет добавлен в Фазе 2 (Часть 2).
          </p>
        </div>
      </div>
    </div>
  )
}
