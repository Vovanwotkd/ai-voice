# 🤖 AI Voice Hostess Bot

Голосовой бот-хостес для ресторана с RAG-системой и управляемой админкой.

## 📋 Описание проекта

Интеллектуальный голосовой помощник для ресторанов, который:

- ✅ Принимает звонки и общается с гостями
- ✅ Бронирует столики (дата, время, количество гостей)
- ✅ Отвечает на вопросы используя RAG (меню, цены, акции, часы работы)
- ✅ Управляется через веб-админку с редактором промптов
- ✅ Поддерживает hot reload промптов без перезапуска
- ✅ Логирует все разговоры для аналитики

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│       React Admin Panel                 │
│   - Chat тестирование                   │
│   - Prompt Editor (Monaco)              │
│   - RAG Knowledge Base Manager          │
│   - История разговоров                  │
└──────────────┬──────────────────────────┘
               │ REST API + WebSocket
               ↓
┌─────────────────────────────────────────┐
│       FastAPI Backend                   │
│   - LLM Integration (Claude/GPT/Yandex) │
│   - RAG System (ChromaDB + Embeddings)  │
│   - Yandex STT/TTS                      │
│   - Conversation Management             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   PostgreSQL + Redis + ChromaDB         │
└─────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### Требования

- Docker & Docker Compose
- Git
- Node.js 18+ (для локальной разработки frontend)
- Python 3.11+ (для локальной разработки backend)

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ai-voice
```

### 2. Настройка переменных окружения

```bash
# Скопируйте .env.example и заполните значения
cp .env.example .env
```

Обязательные переменные:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password

# API Keys (минимум один LLM провайдер)
ANTHROPIC_API_KEY=sk-ant-xxx          # Для Claude
OPENAI_API_KEY=sk-xxx                 # Для GPT-4 или embeddings
YANDEX_API_KEY=xxx                    # Для YandexGPT/STT/TTS
YANDEX_FOLDER_ID=xxx

# LLM Provider
LLM_PROVIDER=claude  # claude | openai | yandex

# Restaurant
RESTAURANT_NAME=Ваш Ресторан
RESTAURANT_PHONE=+7-XXX-XXX-XX-XX
RESTAURANT_ADDRESS=Москва, ул. Примерная, 1
```

### 3. Запуск с Docker Compose (рекомендуется)

```bash
# Production
docker-compose up -d

# Development (с hot reload)
docker-compose -f docker-compose.dev.yml up
```

Приложение будет доступно:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### 4. Проверка здоровья

```bash
curl http://localhost:8000/api/health
```

## 🛠️ Разработка

### Backend (FastAPI)

```bash
cd backend

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Установка зависимостей
pip install -r requirements.txt

# Миграции
alembic upgrade head

# Запуск dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev server
npm run dev

# Build для production
npm run build
```

### Тесты

```bash
# Backend тесты
cd backend
pytest --cov=app

# Frontend тесты
cd frontend
npm run test

# Lint
npm run lint
```

## 📊 Структура проекта

```
ai-voice/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       └── deploy.yml
│
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   │   ├── rag/        # RAG система
│   │   │   ├── llm_service.py
│   │   │   └── yandex_*.py
│   │   └── main.py
│   ├── tests/
│   ├── migrations/         # Alembic
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   │   ├── Chat/
│   │   │   ├── Prompts/
│   │   │   └── RAG/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml      # Production
├── docker-compose.dev.yml  # Development
├── .env.example
└── README.md
```

## 🎯 Основные фичи

### MVP (Этап 1-3)
- [x] Текстовый чат с ботом
- [x] LLM интеграция (Claude/GPT-4/YandexGPT)
- [x] Prompt Editor с Monaco
- [x] Hot Reload промптов
- [x] История разговоров
- [x] Yandex TTS для синтеза речи

### RAG (Этап 4)
- [ ] Загрузка документов (PDF, DOCX, TXT)
- [ ] Vector search (ChromaDB)
- [ ] Интеграция RAG в ответы бота
- [ ] UI для управления базой знаний

### Телефония (Этап 5)
- [ ] Vocode интеграция
- [ ] SIP телефония
- [ ] Yandex STT для распознавания речи
- [ ] Call routing

### Production (Этап 6)
- [ ] JWT аутентификация
- [ ] Rate limiting
- [ ] Мониторинг (Sentry)
- [ ] Metrics & Analytics

## 🔧 API Endpoints

### Chat API

```bash
# Отправить сообщение боту
POST /api/chat/message
{
  "message": "Здравствуйте, хочу забронировать столик",
  "conversation_id": "optional-uuid"
}

# Получить историю разговоров
GET /api/chat/history?limit=50&offset=0

# Получить конкретный разговор
GET /api/chat/conversation/{conversation_id}
```

### Prompts API

```bash
# Получить активный промпт
GET /api/prompts/active

# Обновить промпт
PUT /api/prompts/{id}
{
  "content": "Ты - хостес ресторана..."
}

# Hot Reload промптов
POST /api/prompts/reload
```

### RAG API (будет добавлено)

```bash
# Загрузить документ
POST /api/rag/upload

# Поиск по базе знаний
POST /api/rag/search
{
  "query": "Есть ли вегетарианские блюда?",
  "top_k": 5
}

# Список документов
GET /api/rag/documents
```

## 🚀 Деплой на сервер

### Требования к серверу

**Минимальные:**
- CPU: 2-4 ядра
- RAM: 4-8 GB
- SSD: 50 GB
- Ubuntu 22.04 LTS

**Рекомендуемые провайдеры:**
- Timeweb VPS-2 (~500₽/мес)
- VK Cloud S1-4-20 (~700₽/мес)
- Yandex Cloud s2.micro (~800₽/мес)

### Автоматический деплой через GitHub Actions

1. **Настройте secrets в GitHub:**

```
Settings → Secrets and variables → Actions → New repository secret
```

Добавьте:
- `SERVER_HOST` - IP адрес вашего сервера
- `SERVER_USER` - SSH пользователь (обычно `root`)
- `SSH_PRIVATE_KEY` - приватный SSH ключ
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub token
- `TELEGRAM_BOT_TOKEN` - для уведомлений (опционально)
- `TELEGRAM_CHAT_ID` - для уведомлений (опционально)

2. **Подготовьте сервер:**

```bash
# SSH на сервер
ssh root@your-server-ip

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установите Docker Compose
apt install docker-compose-plugin

# Создайте директорию проекта
mkdir -p /opt/hostess-bot
cd /opt/hostess-bot

# Клонируйте репозиторий
git clone <repository-url> .

# Создайте .env файл
nano .env
# (заполните переменные окружения)

# Первый запуск
docker-compose up -d
```

3. **Push в main → автоматический деплой:**

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions автоматически:
- Запустит тесты
- Соберет Docker образы
- Задеплоит на сервер
- Отправит уведомление в Telegram

### Ручной деплой

```bash
# На сервере
cd /opt/hostess-bot

# Получить последние изменения
git pull origin main

# Пересобрать и перезапустить
docker-compose down
docker-compose up -d --build

# Применить миграции
docker-compose exec backend alembic upgrade head

# Проверить логи
docker-compose logs -f
```

## 🔐 Безопасность

### Обязательно:
- [ ] Измените дефолтные пароли в `.env`
- [ ] Используйте сильный `SECRET_KEY`
- [ ] Настройте firewall (открыть только 80, 443, 22)
- [ ] Настройте SSL сертификат (Let's Encrypt)
- [ ] Ограничьте CORS origins

### Рекомендуется:
- [ ] Настройте rate limiting
- [ ] Добавьте JWT аутентификацию для админки
- [ ] Настройте backup базы данных
- [ ] Настройте мониторинг (Sentry, Grafana)

## 📝 Переменные окружения

Полный список переменных в [.env.example](.env.example):

| Переменная | Описание | Обязательна |
|------------|----------|-------------|
| `DB_USER` | PostgreSQL пользователь | ✅ |
| `DB_PASSWORD` | PostgreSQL пароль | ✅ |
| `DATABASE_URL` | Полный URL БД | ✅ |
| `REDIS_URL` | Redis URL | ✅ |
| `ANTHROPIC_API_KEY` | Claude API ключ | ⚠️* |
| `OPENAI_API_KEY` | OpenAI API ключ | ⚠️* |
| `YANDEX_API_KEY` | Yandex Cloud API ключ | ⚠️* |
| `LLM_PROVIDER` | Провайдер LLM (claude/openai/yandex) | ✅ |
| `RESTAURANT_NAME` | Название ресторана | ✅ |
| `SECRET_KEY` | Secret key для JWT | ✅ |

*Нужен минимум один LLM провайдер

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend

# Проверьте подключение к БД
docker-compose exec backend python -c "from app.database import engine; engine.connect()"
```

### Frontend не подключается к API

```bash
# Проверьте CORS настройки в backend/.env
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Проверьте API URL в frontend
VITE_API_URL=http://localhost:8000
```

### Миграции не применяются

```bash
# Вручную примените миграции
docker-compose exec backend alembic upgrade head

# Проверьте версию
docker-compose exec backend alembic current
```

### Out of Memory

```bash
# Проверьте использование памяти
docker stats

# Увеличьте RAM на сервере или оптимизируйте:
# - Уменьшите max_tokens в LLM
# - Используйте более легкую модель (claude-haiku, gpt-3.5)
# - Настройте swap
```

## 📊 Мониторинг

### Health checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Database connection
curl http://localhost:8000/api/health/db

# Redis connection
curl http://localhost:8000/api/health/redis
```

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только errors
docker-compose logs -f | grep ERROR
```

### Метрики

```bash
# Статистика контейнеров
docker stats

# Размер базы данных
docker-compose exec postgres psql -U postgres -d hostess_db -c "SELECT pg_size_pretty(pg_database_size('hostess_db'));"
```

## 💰 Стоимость эксплуатации

**Примерный расчет для 50 звонков/день:**

| Сервис | Стоимость/мес |
|--------|---------------|
| VPS (4GB RAM) | ₽500-1500 |
| Claude API (1M tokens) | ~$3 |
| Yandex STT/TTS | ~₽1000 |
| OpenAI Embeddings | ~$5 |
| **Итого** | **₽2500-4000** |

**Оптимизация:**
- Используйте Claude Haiku вместо Sonnet ($0.25 vs $3 за 1M tokens)
- Кешируйте TTS ответы
- Используйте YandexGPT для России (дешевле Claude)

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 📞 Поддержка

- 📧 Email: support@your-domain.com
- 💬 Telegram: @your_support_bot
- 🐛 Issues: [GitHub Issues](../../issues)

## 🗺️ Roadmap

### v1.0 (MVP) - Текущий этап
- [x] Базовый чат с ботом
- [x] LLM интеграция
- [x] Prompt management
- [ ] Yandex TTS
- [ ] Production deploy

### v1.1 (RAG)
- [ ] Загрузка документов
- [ ] Vector search
- [ ] RAG интеграция

### v1.2 (Voice)
- [ ] Vocode + SIP
- [ ] Телефонные звонки
- [ ] Call analytics

### v2.0 (Advanced)
- [ ] Мультиязычность
- [ ] A/B тестирование промптов
- [ ] CRM интеграция
- [ ] Voice analytics

---

**Built with ❤️ using FastAPI, React, Claude AI, and Yandex Cloud**
