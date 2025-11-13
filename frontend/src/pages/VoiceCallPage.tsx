import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { vocodeApi } from '@/api/vocode'

type CallState = 'idle' | 'connecting' | 'active' | 'ending' | 'ended'

interface TranscriptEntry {
  type: 'user' | 'agent'
  text: string
  timestamp: Date
}

export default function VoiceCallPage() {
  const [callState, setCallState] = useState<CallState>('idle')
  const [callId, setCallId] = useState<string | null>(null)
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState<number>(0)

  // Refs for WebSocket and audio
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const audioQueueRef = useRef<Float32Array[]>([])

  // Get Vocode configuration
  const { data: config } = useQuery({
    queryKey: ['vocode-config'],
    queryFn: vocodeApi.getConfig,
  })

  // Start call mutation
  const startCallMutation = useMutation({
    mutationFn: vocodeApi.startCall,
    onSuccess: async (data) => {
      setCallId(data.call_id)
      setCallState('connecting')
      setTranscript([])
      setError(null)

      // Connect to WebSocket
      await connectWebSocket(data.call_id)
    },
    onError: (error: any) => {
      setError(`Failed to start call: ${error.message}`)
      setCallState('idle')
    },
  })

  // End call mutation
  const endCallMutation = useMutation({
    mutationFn: (callId: string) => vocodeApi.endCall(callId),
    onSuccess: () => {
      disconnectCall()
    },
  })

  const connectWebSocket = async (callId: string) => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      mediaStreamRef.current = stream

      // Create audio context
      const audioContext = new AudioContext({ sampleRate: 16000 })
      audioContextRef.current = audioContext

      // Create WebSocket connection
      const wsUrl = vocodeApi.getWebSocketUrl(callId)
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        console.log('WebSocket connected')
        setCallState('active')

        // Start sending audio
        startAudioCapture(stream, audioContext, ws)
      }

      ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          // JSON message (transcription, agent response, etc.)
          try {
            const message = JSON.parse(event.data)
            handleWebSocketMessage(message)
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e)
          }
        } else {
          // Binary audio data from agent
          playAudioChunk(event.data)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
        setCallState('ended')
      }
    } catch (error: any) {
      console.error('Failed to connect:', error)
      setError(`Failed to connect: ${error.message}`)
      setCallState('idle')
    }
  }

  const startAudioCapture = (
    stream: MediaStream,
    audioContext: AudioContext,
    ws: WebSocket
  ) => {
    const source = audioContext.createMediaStreamSource(stream)

    // Create script processor for audio capture
    const processor = audioContext.createScriptProcessor(4096, 1, 1)
    processorRef.current = processor

    processor.onaudioprocess = (e) => {
      if (ws.readyState !== WebSocket.OPEN) return

      const inputData = e.inputBuffer.getChannelData(0)

      // Calculate audio level for visualization
      const sum = inputData.reduce((acc, val) => acc + Math.abs(val), 0)
      const level = sum / inputData.length
      setAudioLevel(Math.min(level * 10, 1)) // Scale for visualization

      // Convert Float32Array to Int16Array (PCM 16-bit)
      const pcmData = new Int16Array(inputData.length)
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]))
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff
      }

      // Send to WebSocket
      ws.send(pcmData.buffer)
    }

    source.connect(processor)
    processor.connect(audioContext.destination)
  }

  const playAudioChunk = async (arrayBuffer: ArrayBuffer) => {
    if (!audioContextRef.current) return

    try {
      // Convert Int16 PCM to Float32
      const pcmData = new Int16Array(arrayBuffer)
      const floatData = new Float32Array(pcmData.length)

      for (let i = 0; i < pcmData.length; i++) {
        floatData[i] = pcmData[i] / (pcmData[i] < 0 ? 0x8000 : 0x7fff)
      }

      // Add to queue for playback
      audioQueueRef.current.push(floatData)

      // Play if not already playing
      if (audioQueueRef.current.length === 1) {
        playNextChunk()
      }
    } catch (error) {
      console.error('Error playing audio:', error)
    }
  }

  const playNextChunk = async () => {
    if (!audioContextRef.current || audioQueueRef.current.length === 0) return

    const audioContext = audioContextRef.current
    const chunk = audioQueueRef.current.shift()!

    // Create buffer and play
    const buffer = audioContext.createBuffer(1, chunk.length, 16000)
    buffer.getChannelData(0).set(chunk)

    const source = audioContext.createBufferSource()
    source.buffer = buffer
    source.connect(audioContext.destination)

    source.onended = () => {
      // Play next chunk
      if (audioQueueRef.current.length > 0) {
        playNextChunk()
      }
    }

    source.start()
  }

  const handleWebSocketMessage = (message: any) => {
    console.log('WebSocket message:', message)

    switch (message.type) {
      case 'transcription':
        if (message.is_final) {
          setTranscript((prev) => [
            ...prev,
            { type: 'user', text: message.text, timestamp: new Date() },
          ])
        }
        break

      case 'agent_response':
        setTranscript((prev) => [
          ...prev,
          { type: 'agent', text: message.text, timestamp: new Date() },
        ])
        break

      case 'error':
        setError(message.message)
        break
    }
  }

  const disconnectCall = () => {
    // Stop audio capture
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Clear audio queue
    audioQueueRef.current = []

    setCallState('ended')
    setAudioLevel(0)
  }

  const handleStartCall = () => {
    startCallMutation.mutate({
      voice: 'alena',
      use_rag: true,
    })
  }

  const handleEndCall = () => {
    if (callId) {
      setCallState('ending')
      endCallMutation.mutate(callId)
    } else {
      disconnectCall()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectCall()
    }
  }, [])

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">
          Голосовой звонок (WebRTC)
        </h1>

        {/* Call Controls */}
        <div className="flex flex-col items-center gap-6 mb-8">
          {/* Status */}
          <div className="text-center">
            <div className="text-lg font-medium text-gray-700 mb-2">
              {callState === 'idle' && 'Готов к звонку'}
              {callState === 'connecting' && 'Подключение...'}
              {callState === 'active' && 'Звонок активен'}
              {callState === 'ending' && 'Завершение...'}
              {callState === 'ended' && 'Звонок завершен'}
            </div>

            {/* Audio Level Indicator */}
            {callState === 'active' && (
              <div className="flex items-center justify-center gap-2 mb-4">
                <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all duration-100"
                    style={{ width: `${audioLevel * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-500">Уровень звука</span>
              </div>
            )}
          </div>

          {/* Call Button */}
          {callState === 'idle' || callState === 'ended' ? (
            <button
              onClick={handleStartCall}
              disabled={startCallMutation.isPending}
              className="w-16 h-16 bg-green-500 text-white rounded-full hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center text-2xl shadow-lg"
            >
              📞
            </button>
          ) : (
            <button
              onClick={handleEndCall}
              disabled={callState === 'ending'}
              className="w-16 h-16 bg-red-500 text-white rounded-full hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center text-2xl shadow-lg"
            >
              ❌
            </button>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <p className="font-medium">Ошибка:</p>
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Transcript */}
        <div className="border-t border-gray-200 pt-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Транскрипт разговора
          </h2>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {transcript.length === 0 ? (
              <p className="text-gray-400 text-center py-8">
                Начните звонок, чтобы увидеть транскрипт
              </p>
            ) : (
              transcript.map((entry, index) => (
                <div
                  key={index}
                  className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-md px-4 py-2 rounded-lg ${
                      entry.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="text-sm">{entry.text}</p>
                    <p
                      className={`text-xs mt-1 ${entry.type === 'user' ? 'text-blue-100' : 'text-gray-500'}`}
                    >
                      {entry.timestamp.toLocaleTimeString('ru-RU')}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Configuration Info */}
        {config && (
          <div className="border-t border-gray-200 mt-6 pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Конфигурация
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">Голос:</span> Alena
              </div>
              <div>
                <span className="font-medium">Частота:</span>{' '}
                {config.audio_config.sample_rate} Hz
              </div>
              <div>
                <span className="font-medium">RAG:</span> Включен
              </div>
              <div>
                <span className="font-medium">Кодирование:</span>{' '}
                {config.audio_config.encoding}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
