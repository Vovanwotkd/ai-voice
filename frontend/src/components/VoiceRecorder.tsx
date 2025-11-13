import { useState, useRef, useEffect } from 'react'

interface VoiceMessage {
  type: 'status' | 'transcription' | 'response' | 'error'
  status?: 'listening' | 'processing' | 'speaking'
  text?: string
  audio?: string
  conversation_id?: string
  latency_ms?: number
  message?: string
}

interface VoiceRecorderProps {
  conversationId: string | null
  onMessage: (userText: string, botText: string, audioUrl: string, conversationId: string) => void
}

export default function VoiceRecorder({ conversationId, onMessage }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [status, setStatus] = useState<string>('')
  const [transcription, setTranscription] = useState<string>('')

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // WebSocket connection
  const connectWebSocket = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws/voice'

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const message: VoiceMessage = JSON.parse(event.data)
      console.log('WebSocket message:', message)

      if (message.type === 'status') {
        const statusText = {
          listening: '🎤 Слушаю...',
          processing: '🤔 Думаю...',
          speaking: '🔊 Отвечаю...'
        }[message.status || '']
        setStatus(statusText || '')
      } else if (message.type === 'transcription') {
        setTranscription(message.text || '')
      } else if (message.type === 'response') {
        // Play audio response
        if (message.audio) {
          playAudioResponse(message.audio)
        }

        // Add messages to chat
        if (message.text && transcription) {
          onMessage(
            transcription,
            message.text,
            message.audio || '',
            message.conversation_id || conversationId || ''
          )
        }

        setStatus('')
        setTranscription('')
      } else if (message.type === 'error') {
        console.error('Voice error:', message.message)
        alert(`Ошибка: ${message.message}`)
        setStatus('')
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    wsRef.current = ws
  }

  // Play audio response
  const playAudioResponse = (audioBase64: string) => {
    try {
      // Decode base64 audio
      const audioBlob = base64ToBlob(audioBase64, 'audio/ogg')
      const audioUrl = URL.createObjectURL(audioBlob)

      // Create audio element and play
      if (audioRef.current) {
        audioRef.current.pause()
      }

      const audio = new Audio(audioUrl)
      audioRef.current = audio

      audio.play().catch(error => {
        console.error('Failed to play audio:', error)
      })
    } catch (error) {
      console.error('Error playing audio:', error)
    }
  }

  // Convert base64 to Blob
  const base64ToBlob = (base64: string, contentType: string): Blob => {
    const byteCharacters = atob(base64)
    const byteNumbers = new Array(byteCharacters.length)

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }

    const byteArray = new Uint8Array(byteNumbers)
    return new Blob([byteArray], { type: contentType })
  }

  // Start recording
  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Create MediaRecorder with OGG Opus format
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        // Combine all chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

        // Convert to base64
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1]

          // Send to WebSocket
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              data: base64Audio,
              format: 'oggopus',
              conversation_id: conversationId
            }))
          }
        }
        reader.readAsDataURL(audioBlob)

        // Stop tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)

    } catch (error) {
      console.error('Failed to start recording:', error)
      alert('Не удалось получить доступ к микрофону')
    }
  }

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  // Toggle recording
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      if (!isConnected) {
        connectWebSocket()
      }
      startRecording()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (audioRef.current) {
        audioRef.current.pause()
      }
    }
  }, [])

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Recording Button */}
      <button
        onClick={toggleRecording}
        disabled={!isConnected && !isRecording}
        className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all ${
          isRecording
            ? 'bg-red-500 hover:bg-red-600 animate-pulse'
            : 'bg-blue-600 hover:bg-blue-700'
        } text-white disabled:bg-gray-300 disabled:cursor-not-allowed`}
        title={isRecording ? 'Остановить запись' : 'Начать запись'}
      >
        {isRecording ? '⏹️' : '🎤'}
      </button>

      {/* Connection Status */}
      {!isConnected && !isRecording && (
        <button
          onClick={connectWebSocket}
          className="text-xs text-gray-500 hover:text-blue-600 underline"
        >
          Подключиться
        </button>
      )}

      {/* Status Indicator */}
      {status && (
        <div className="text-sm text-gray-600 animate-pulse">
          {status}
        </div>
      )}

      {/* Transcription */}
      {transcription && (
        <div className="text-sm text-gray-700 bg-gray-100 px-3 py-1 rounded-lg max-w-xs">
          {transcription}
        </div>
      )}
    </div>
  )
}
