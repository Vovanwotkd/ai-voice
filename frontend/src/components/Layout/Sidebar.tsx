import { Link, useLocation } from 'react-router-dom'

const navigation = [
  { name: 'Чат', href: '/chat', icon: '💬' },
  { name: 'Промпты', href: '/prompts', icon: '📝' },
  { name: 'История', href: '/history', icon: '📚' },
  { name: 'Дашборд', href: '/dashboard', icon: '📊' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-6">
        <h1 className="text-xl font-bold">🤖 AI Hostess Bot</h1>
        <p className="text-sm text-gray-400 mt-1">Админ-панель</p>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`
                flex items-center px-3 py-2 rounded-lg transition-colors
                ${
                  isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }
              `}
            >
              <span className="text-xl mr-3">{item.icon}</span>
              <span className="font-medium">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-gray-800 text-sm text-gray-400">
        v1.0.0 | Фаза 2 MVP
      </div>
    </div>
  )
}
