export default function PromptsPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">📝 Управление промптами</h1>
        <p className="text-gray-600 mb-6">
          Здесь будет редактор системных промптов с Monaco Editor.
        </p>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 font-medium">🚧 В разработке</p>
          <p className="text-yellow-600 text-sm mt-1">
            Prompt Editor с hot reload будет добавлен в Фазе 2 (Часть 2).
          </p>
        </div>
      </div>
    </div>
  )
}
