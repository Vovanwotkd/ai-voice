# Vocode Implementation - Phase 5

## Что реализовано

### Backend Components

1. **YandexTranscriber** ([backend/app/services/yandex_transcriber.py](backend/app/services/yandex_transcriber.py))
   - Streaming речевое распознавание через Yandex SpeechKit v3
   - Поддержка partial и final транскрипций
   - Аутентификация через API key (без IAM token)
   - Интеграция с Vocode framework

2. **YandexSynthesizer** ([backend/app/services/yandex_synthesizer.py](backend/app/services/yandex_synthesizer.py))
   - Streaming синтез речи через Yandex SpeechKit v3
   - Поддержка множества голосов (Alena, Jane, Filipp и др.)
   - Настройки скорости, тона, громкости
   - PCM 16kHz аудио для WebRTC

3. **HostessAgent** ([backend/app/services/hostess_agent.py](backend/app/services/hostess_agent.py))
   - AI-агент с интеграцией RAG
   - Использует базу знаний для точных ответов
   - Сохранение истории разговора в БД
   - Настраиваемые system prompts

4. **WebRTC Endpoints** ([backend/app/api/vocode_calls.py](backend/app/api/vocode_calls.py))
   - `/api/vocode/start` - Инициализация звонка
   - `/api/vocode/ws/{call_id}` - WebSocket для аудио стриминга
   - `/api/vocode/status/{call_id}` - Статус звонка
   - `/api/vocode/config` - Конфигурация (голоса, промпты)

### Frontend Components

1. **VoiceCallPage** ([frontend/src/pages/VoiceCallPage.tsx](frontend/src/pages/VoiceCallPage.tsx))
   - WebRTC аудио захват и воспроизведение
   - Визуализация уровня звука
   - Транскрипт в реальном времени
   - Управление звонком (старт/стоп)

2. **Vocode API Client** ([frontend/src/api/vocode.ts](frontend/src/api/vocode.ts))
   - TypeScript клиент для Vocode endpoints
   - WebSocket connection management

### Обновленные зависимости

```txt
# Backend - requirements.txt
vocode==0.1.112.1
aiohttp==3.9.1
grpcio==1.60.0
grpcio-tools==1.60.0
yandex-speechkit==2.2.2
```

## Как запустить

### 1. Пересобрать backend

```bash
# Пересобрать Docker image с новыми зависимостями
docker compose build backend

# Перезапустить контейнеры
docker compose down
docker compose up -d
```

### 2. Проверить логи

```bash
# Проверить что backend запустился без ошибок
docker compose logs backend

# Должны увидеть:
# ✅ Database initialized
# ✅ Default prompt initialized
```

### 3. Открыть админ-панель

1. Перейти в браузере: http://localhost:3000
2. Войти в систему
3. Нажать на "Голосовой звонок" в меню

### 4. Протестировать WebRTC звонок

1. Нажать зеленую кнопку 📞 для начала звонка
2. Разрешить доступ к микрофону в браузере
3. Дождаться приветствия от агента
4. Говорить вопросы о ресторане
5. Смотреть транскрипт в реальном времени
6. Нажать красную кнопку ❌ для завершения

## Архитектура

```
Browser (WebRTC)
    ↓ [PCM Audio]
WebSocket (/api/vocode/ws/{call_id})
    ↓
YandexTranscriber (STT)
    ↓ [Text]
HostessAgent (with RAG)
    ↓ [Response Text]
YandexSynthesizer (TTS)
    ↓ [PCM Audio]
WebSocket → Browser
```

## Поток данных

1. **User speaks** → Browser captures audio (16kHz PCM)
2. **Browser** → WebSocket sends audio chunks
3. **YandexTranscriber** → Sends to Yandex SpeechKit v3 gRPC
4. **Yandex STT** → Returns transcription
5. **HostessAgent** → Receives text, queries RAG, generates response
6. **YandexSynthesizer** → Synthesizes response via Yandex TTS v3
7. **WebSocket** → Streams audio back to browser
8. **Browser** → Plays synthesized speech

## Особенности реализации

### Аутентификация Yandex API

- **Упрощенный подход**: Используем API key напрямую
- **Без IAM token**: API key достаточно для streaming API v3
- **Метаданные gRPC**: `('authorization', f'Api-Key {api_key}')`

### RAG интеграция

- HostessAgent автоматически использует базу знаний
- Semantic search в ChromaDB для релевантного контекста
- История разговора сохраняется в PostgreSQL

### WebRTC аудио

- **Формат**: LINEAR16 PCM, 16kHz, mono
- **Обработка**: Browser → Float32 → Int16 → WebSocket → Int16 → Float32 → Speaker
- **Буферизация**: Очередь для плавного воспроизведения

## Доступные голоса Yandex

**Женские:**
- `alena` - Дружелюбный (рекомендуется)
- `jane` - Нейтральный
- `omazh` - Анимированный
- `dasha` - Спокойный
- `julia` - Экспрессивный
- `lera` - Молодой
- `marina` - Профессиональный

**Мужские:**
- `filipp` - Нейтральный
- `ermil` - Дружелюбный
- `madirus` - Глубокий
- `zahar` - Профессиональный

## Следующие шаги (SIP для Beeline)

1. Настроить Twilio или Telnyx для SIP интеграции
2. Создать SIP endpoint в Vocode
3. Настроить маршрутизацию звонков от Beeline
4. Добавить логирование и аналитику звонков
5. Тестирование на реальных звонках

## Troubleshooting

### Backend не запускается

```bash
# Проверить логи
docker compose logs backend

# Если ошибки с зависимостями - пересобрать
docker compose build --no-cache backend
```

### WebSocket не подключается

- Проверить что backend запущен: `docker compose ps`
- Проверить CORS настройки в `.env`
- Проверить WebSocket URL в браузере DevTools

### Нет звука

- Проверить разрешения микрофона в браузере
- Проверить что используется HTTPS или localhost
- Открыть DevTools → Console для ошибок

### Транскрипция не работает

- Проверить `YANDEX_API_KEY` в `.env`
- Проверить логи backend для gRPC ошибок
- Убедиться что API key валидный для SpeechKit v3

## API Endpoints

### POST /api/vocode/start
Начать новый голосовой звонок

**Request:**
```json
{
  "voice": "alena",
  "use_rag": true,
  "system_prompt": "..."
}
```

**Response:**
```json
{
  "call_id": "uuid",
  "status": "initialized",
  "websocket_url": "/api/vocode/ws/{call_id}"
}
```

### WS /api/vocode/ws/{call_id}
WebSocket для аудио стриминга

**Client → Server:**
- Binary: Int16 PCM audio chunks
- Text: Control messages (`end_call`)

**Server → Client:**
- Binary: Int16 PCM audio chunks
- JSON: Transcriptions, agent responses, errors

### GET /api/vocode/config
Получить конфигурацию

**Response:**
```json
{
  "voices": {...},
  "system_prompts": {...},
  "audio_config": {
    "sample_rate": 16000,
    "encoding": "LINEAR16_PCM"
  }
}
```

## Структура файлов

```
backend/
├── app/
│   ├── api/
│   │   └── vocode_calls.py          # WebRTC endpoints
│   └── services/
│       ├── yandex_transcriber.py    # STT
│       ├── yandex_synthesizer.py    # TTS
│       └── hostess_agent.py         # AI Agent
│
frontend/
├── src/
│   ├── api/
│   │   └── vocode.ts                # API client
│   └── pages/
│       └── VoiceCallPage.tsx        # UI
```

## Конфигурация (.env)

Необходимые переменные:

```env
# Yandex SpeechKit v3
YANDEX_API_KEY=AQVNxxxxxxxxx
YANDEX_FOLDER_ID=b1gxxxxxxxxx  # Опционально

# LLM Provider
LLM_PROVIDER=yandex  # или claude/openai

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dbname
```

## Метрики и логирование

- **Логи**: Docker logs (`docker compose logs backend`)
- **Статус звонков**: GET `/api/vocode/active`
- **История**: Автоматически сохраняется в БД
- **Аналитика**: Dashboard (TODO)

---

**Версия**: 1.1.0 - Фаза 5 Vocode
**Дата**: 2025
**Статус**: ✅ Готов к тестированию
