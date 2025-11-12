export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Управление ботом-хостес
          </h2>
          <p className="text-sm text-gray-500">
            Тестирование и настройка голосового помощника
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            ● Онлайн
          </span>
        </div>
      </div>
    </header>
  )
}
