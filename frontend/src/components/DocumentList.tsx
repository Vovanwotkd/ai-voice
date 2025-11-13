import { Document } from '@/api/documents'

interface DocumentListProps {
  documents: Document[]
  onDelete: (id: string) => void
  onReindex: (id: string) => void
  isDeleting: boolean
  isReindexing: boolean
}

export default function DocumentList({
  documents,
  onDelete,
  onReindex,
  isDeleting,
  isReindexing,
}: DocumentListProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-gray-700">Название</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">Тип</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">Статус</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">Размер</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">Чанков</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">Дата</th>
            <th className="text-right py-3 px-4 font-medium text-gray-700">
              Действия
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr
              key={doc.id}
              className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getFileIcon(doc.type)}</span>
                  <div>
                    <p className="font-medium text-gray-800 line-clamp-1">
                      {doc.name}
                    </p>
                    {doc.error_message && (
                      <p className="text-xs text-red-600 line-clamp-1 mt-1">
                        {doc.error_message}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="py-3 px-4">
                <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded uppercase">
                  {doc.type}
                </span>
              </td>
              <td className="py-3 px-4">{getStatusBadge(doc.status)}</td>
              <td className="py-3 px-4 text-sm text-gray-600">
                {formatFileSize(doc.file_size)}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">
                {doc.chunks_count > 0 ? (
                  <span className="font-medium text-blue-600">{doc.chunks_count}</span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">
                {new Date(doc.created_at).toLocaleString('ru-RU', {
                  day: '2-digit',
                  month: '2-digit',
                  year: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center justify-end gap-2">
                  {doc.status === 'failed' && (
                    <button
                      onClick={() => onReindex(doc.id)}
                      disabled={isReindexing}
                      className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      title="Переиндексировать"
                    >
                      🔄 Повторить
                    </button>
                  )}
                  {doc.status === 'indexed' && (
                    <button
                      onClick={() => onReindex(doc.id)}
                      disabled={isReindexing}
                      className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      title="Переиндексировать"
                    >
                      🔄
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(doc.id)}
                    disabled={isDeleting}
                    className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    title="Удалить"
                  >
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getFileIcon(type: string): string {
  const icons: Record<string, string> = {
    pdf: '📕',
    docx: '📘',
    txt: '📄',
    md: '📝',
  }
  return icons[type] || '📄'
}

function getStatusBadge(status: string): JSX.Element {
  const configs: Record<
    string,
    { label: string; bg: string; text: string; icon: string }
  > = {
    pending: {
      label: 'Ожидание',
      bg: 'bg-gray-100',
      text: 'text-gray-700',
      icon: '⏸️',
    },
    processing: {
      label: 'Обработка',
      bg: 'bg-orange-100',
      text: 'text-orange-700',
      icon: '⏳',
    },
    indexed: {
      label: 'Готов',
      bg: 'bg-green-100',
      text: 'text-green-700',
      icon: '✅',
    },
    failed: {
      label: 'Ошибка',
      bg: 'bg-red-100',
      text: 'text-red-700',
      icon: '❌',
    },
  }

  const config = configs[status] || configs.pending

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 ${config.bg} ${config.text} text-xs font-medium rounded`}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}
