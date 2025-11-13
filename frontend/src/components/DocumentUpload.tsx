import { useState, useCallback, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { documentsApi } from '@/api/documents'

interface DocumentUploadProps {
  onUploadSuccess?: () => void
}

export default function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({ type: null, message: '' })
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadMutation = useMutation({
    mutationFn: documentsApi.uploadDocument,
    onSuccess: (data) => {
      setUploadStatus({
        type: 'success',
        message: `✅ ${data.message}`,
      })
      setTimeout(() => {
        setUploadStatus({ type: null, message: '' })
      }, 5000)
      onUploadSuccess?.()
    },
    onError: (error: any) => {
      setUploadStatus({
        type: 'error',
        message: `❌ Ошибка: ${error.response?.data?.detail || error.message}`,
      })
      setTimeout(() => {
        setUploadStatus({ type: null, message: '' })
      }, 5000)
    },
  })

  const handleFile = useCallback(
    (file: File) => {
      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
      ]
      const allowedExtensions = ['.pdf', '.docx', '.txt', '.md']

      const isValidType = allowedTypes.includes(file.type)
      const isValidExtension = allowedExtensions.some((ext) =>
        file.name.toLowerCase().endsWith(ext)
      )

      if (!isValidType && !isValidExtension) {
        setUploadStatus({
          type: 'error',
          message: '❌ Неподдерживаемый формат файла. Используйте PDF, DOCX, TXT или MD',
        })
        return
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        setUploadStatus({
          type: 'error',
          message: '❌ Файл слишком большой. Максимум 10 МБ',
        })
        return
      }

      uploadMutation.mutate(file)
    },
    [uploadMutation]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className="space-y-4">
      {/* Drag & drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200
          ${isDragging ? 'border-blue-500 bg-blue-50 scale-105' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}
          ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploadMutation.isPending}
        />

        <div className="text-5xl mb-3">
          {uploadMutation.isPending ? '⏳' : isDragging ? '📂' : '📄'}
        </div>

        {uploadMutation.isPending ? (
          <div>
            <p className="text-lg font-medium text-gray-700 mb-2">Загрузка документа...</p>
            <p className="text-sm text-gray-500">
              Файл обрабатывается и индексируется
            </p>
            <div className="mt-4 w-full max-w-xs mx-auto bg-gray-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full animate-pulse w-3/4"></div>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-lg font-medium text-gray-700 mb-2">
              {isDragging
                ? 'Отпустите файл для загрузки'
                : 'Перетащите файл сюда или нажмите для выбора'}
            </p>
            <p className="text-sm text-gray-500">
              Поддерживаются форматы: PDF, DOCX, TXT, MD (макс. 10 МБ)
            </p>
          </div>
        )}
      </div>

      {/* Status message */}
      {uploadStatus.type && (
        <div
          className={`
            p-4 rounded-lg border
            ${uploadStatus.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}
          `}
        >
          <p className="font-medium">{uploadStatus.message}</p>
        </div>
      )}

      {/* Quick upload buttons */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={handleClick}
          disabled={uploadMutation.isPending}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          📁 Выбрать файл
        </button>

        <div className="text-sm text-gray-500 flex items-center">
          <span>Или перетащите файл в область выше</span>
        </div>
      </div>
    </div>
  )
}
