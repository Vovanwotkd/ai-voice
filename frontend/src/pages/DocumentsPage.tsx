import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/api/documents'
import DocumentUpload from '@/components/DocumentUpload'
import DocumentList from '@/components/DocumentList'

export default function DocumentsPage() {
  const [uploadKey, setUploadKey] = useState(0)
  const queryClient = useQueryClient()

  // Load documents
  const {
    data: documentsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.getDocuments,
    refetchInterval: 5000, // Auto-refresh every 5 seconds to see processing status
  })

  // Load collection stats
  const { data: stats } = useQuery({
    queryKey: ['collection-stats'],
    queryFn: documentsApi.getCollectionStats,
    refetchInterval: 10000,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: documentsApi.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['collection-stats'] })
    },
  })

  // Reindex mutation
  const reindexMutation = useMutation({
    mutationFn: documentsApi.reindexDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleUploadSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['documents'] })
    queryClient.invalidateQueries({ queryKey: ['collection-stats'] })
    setUploadKey((prev) => prev + 1) // Reset upload component
  }, [queryClient])

  const handleDelete = useCallback(
    (id: string) => {
      if (confirm('Вы уверены, что хотите удалить этот документ?')) {
        deleteMutation.mutate(id)
      }
    },
    [deleteMutation]
  )

  const handleReindex = useCallback(
    (id: string) => {
      if (confirm('Переиндексировать этот документ?')) {
        reindexMutation.mutate(id)
      }
    },
    [reindexMutation]
  )

  const documents = documentsData?.documents || []

  // Calculate stats
  const pageStats = {
    total: documentsData?.total || 0,
    indexed: documents.filter((d) => d.status === 'indexed').length,
    processing: documents.filter((d) => d.status === 'processing').length,
    failed: documents.filter((d) => d.status === 'failed').length,
    totalChunks: stats?.total_chunks || 0,
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">📚 База знаний</h1>
        <p className="text-gray-600">
          Управление документами для RAG (Retrieval-Augmented Generation)
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <StatCard
          icon="📄"
          title="Всего документов"
          value={pageStats.total}
          color="blue"
        />
        <StatCard
          icon="✅"
          title="Проиндексировано"
          value={pageStats.indexed}
          color="green"
        />
        <StatCard
          icon="⏳"
          title="Обрабатывается"
          value={pageStats.processing}
          color="orange"
        />
        <StatCard icon="❌" title="Ошибки" value={pageStats.failed} color="red" />
        <StatCard
          icon="🧩"
          title="Чанков в базе"
          value={pageStats.totalChunks}
          color="purple"
        />
      </div>

      {/* Upload section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">⬆️ Загрузка документов</h2>
        <DocumentUpload key={uploadKey} onUploadSuccess={handleUploadSuccess} />
      </div>

      {/* Documents list */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">📋 Список документов</h2>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="text-4xl mb-2">⏳</div>
              <p className="text-gray-600">Загрузка документов...</p>
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-2">⚠️</div>
            <p className="text-red-600">Ошибка загрузки документов</p>
            <p className="text-sm text-gray-500 mt-2">{String(error)}</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">📭</div>
            <p>Нет загруженных документов</p>
            <p className="text-sm mt-2">Загрузите первый документ выше</p>
          </div>
        ) : (
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            onReindex={handleReindex}
            isDeleting={deleteMutation.isPending}
            isReindexing={reindexMutation.isPending}
          />
        )}
      </div>

      {/* Info section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <h3 className="font-bold text-blue-900 mb-2">ℹ️ Информация</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Поддерживаемые форматы: PDF, DOCX, TXT, MD</li>
          <li>• Документы автоматически разбиваются на чанки по ~500 токенов</li>
          <li>
            • Чанки индексируются в векторной базе ChromaDB для семантического поиска
          </li>
          <li>• RAG автоматически используется в чате для более точных ответов</li>
          <li>• Обработка документа занимает 5-30 секунд в зависимости от размера</li>
        </ul>
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
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    red: 'bg-red-50 text-red-600 border-red-200',
  }

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <p className="text-xs font-medium">{title}</p>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}
