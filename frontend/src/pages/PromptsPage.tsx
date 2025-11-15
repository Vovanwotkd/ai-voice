import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Editor from '@monaco-editor/react'
import { promptsApi } from '@/api/prompts'

export default function PromptsPage() {
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState<string>('')
  const [showPreview, setShowPreview] = useState(false)
  const [previewContent, setPreviewContent] = useState<string>('')
  const queryClient = useQueryClient()

  // Load all prompts with aggressive caching
  const { data: prompts, isLoading: promptsLoading, error: promptsError } = useQuery({
    queryKey: ['prompts'],
    queryFn: promptsApi.getAllPrompts,
    staleTime: 5 * 60 * 1000, // 5 minutes - data stays fresh
    gcTime: 30 * 60 * 1000, // 30 minutes - cache retention (React Query v5)
    refetchOnWindowFocus: false, // Don't refetch on window focus
    refetchOnMount: false, // Don't refetch on component mount if cached
  })

  // Load available variables with caching
  const { data: variables } = useQuery({
    queryKey: ['prompt-variables'],
    queryFn: promptsApi.getAvailableVariables,
    staleTime: 10 * 60 * 1000, // 10 minutes - variables rarely change
    gcTime: 60 * 60 * 1000, // 1 hour cache (React Query v5)
    refetchOnWindowFocus: false,
  })

  // Get selected prompt - with array safety check
  const selectedPrompt = Array.isArray(prompts) ? prompts.find((p) => p.id === selectedPromptId) : undefined

  // Update selected content when prompt changes
  useEffect(() => {
    if (selectedPrompt && editedContent !== selectedPrompt.content) {
      setEditedContent(selectedPrompt.content)
    }
  }, [selectedPrompt])

  // Update prompt mutation
  const updatePromptMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPromptId) return
      return promptsApi.updatePrompt(selectedPromptId, {
        content: editedContent,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      alert('✅ Промпт успешно сохранён!')
    },
    onError: () => {
      alert('❌ Ошибка при сохранении промпта')
    },
  })

  // Hot reload mutation
  const reloadMutation = useMutation({
    mutationFn: promptsApi.reloadPrompts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      alert('🔥 Промпты перезагружены!')
    },
    onError: () => {
      alert('❌ Ошибка при перезагрузке промптов')
    },
  })

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: async () => {
      const preview = await promptsApi.previewPrompt(editedContent)
      setPreviewContent(preview)
      setShowPreview(true)
    },
    onError: () => {
      alert('❌ Ошибка при генерации превью')
    },
  })

  const handleSave = () => {
    if (!selectedPrompt) return
    updatePromptMutation.mutate()
  }

  const handlePreview = () => {
    previewMutation.mutate()
  }

  const handleReload = () => {
    reloadMutation.mutate()
  }

  if (promptsLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <p className="text-gray-600">Загрузка промптов...</p>
        </div>
      </div>
    )
  }

  if (promptsError) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="text-4xl mb-2">❌</div>
          <p className="text-gray-600">Ошибка загрузки промптов</p>
          <p className="text-sm text-gray-500 mt-2">{String(promptsError)}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar with prompts list */}
      <div className="w-80 bg-white border-r p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">📝 Промпты</h2>
          <button
            onClick={handleReload}
            disabled={reloadMutation.isPending}
            className="px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg disabled:bg-gray-300 transition-colors"
            title="Hot Reload - перезагрузить промпты из файлов"
          >
            🔥 Reload
          </button>
        </div>

        <div className="space-y-2">
          {Array.isArray(prompts) && prompts.map((prompt) => (
            <button
              key={prompt.id}
              onClick={() => {
                setSelectedPromptId(prompt.id)
                setEditedContent(prompt.content)
                setShowPreview(false)
              }}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedPromptId === prompt.id
                  ? 'bg-blue-50 border-blue-500'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">
                  {prompt.is_active ? '✅' : '⚪'}
                </span>
                <span className="font-medium text-sm">{prompt.name}</span>
              </div>
              {prompt.description && (
                <p className="text-xs text-gray-500 line-clamp-2">
                  {prompt.description}
                </p>
              )}
              <p className="text-xs text-gray-400 mt-1">
                v{prompt.version} • {new Date(prompt.updated_at).toLocaleDateString('ru-RU')}
              </p>
            </button>
          ))}
        </div>

        {/* Variables panel */}
        {variables && (
          <div className="mt-6 p-3 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-bold mb-2">🔧 Доступные переменные:</h3>
            <div className="space-y-1 text-xs text-gray-600">
              {Object.entries(variables).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <code className="text-blue-600">{`{${key}}`}</code>
                  <span className="text-gray-500">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        {selectedPrompt ? (
          <>
            {/* Header */}
            <div className="bg-white border-b px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-bold">{selectedPrompt.name}</h1>
                  <p className="text-sm text-gray-500">
                    {selectedPrompt.description || 'Редактирование промпта'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handlePreview}
                    disabled={previewMutation.isPending}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg disabled:bg-gray-300 transition-colors"
                  >
                    👁️ Preview
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={
                      updatePromptMutation.isPending ||
                      editedContent === selectedPrompt.content
                    }
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    💾 Сохранить
                  </button>
                </div>
              </div>
            </div>

            {/* Editor or Preview */}
            <div className="flex-1 overflow-hidden">
              {showPreview ? (
                <div className="h-full overflow-y-auto bg-gray-50 p-6">
                  <div className="max-w-4xl mx-auto">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-bold">📄 Preview с подстановкой переменных</h2>
                      <button
                        onClick={() => setShowPreview(false)}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm"
                      >
                        ✏️ Вернуться к редактору
                      </button>
                    </div>
                    <div className="bg-white border rounded-lg p-6 whitespace-pre-wrap font-mono text-sm">
                      {previewContent}
                    </div>
                  </div>
                </div>
              ) : (
                <Editor
                  height="100%"
                  defaultLanguage="markdown"
                  value={editedContent}
                  onChange={(value) => setEditedContent(value || '')}
                  theme="vs-light"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    wordWrap: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                  }}
                />
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="text-center">
              <div className="text-6xl mb-4">📝</div>
              <h2 className="text-xl font-semibold text-gray-700 mb-2">
                Выберите промпт для редактирования
              </h2>
              <p className="text-gray-500">
                Выберите промпт из списка слева
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
