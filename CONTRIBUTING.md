# Contributing to AI Voice Hostess Bot

Спасибо за интерес к проекту! Мы рады вашему вкладу.

## 🚀 Быстрый старт для разработчиков

### 1. Fork и клонирование

```bash
# Fork репозиторий на GitHub, затем:
git clone https://github.com/YOUR_USERNAME/ai-voice.git
cd ai-voice
```

### 2. Настройка окружения

```bash
# Скопируйте .env.example
cp .env.example .env

# Отредактируйте .env и добавьте свои API ключи
```

### 3. Запуск development окружения

```bash
# Используя Makefile (рекомендуется)
make dev-build

# Или напрямую docker-compose
docker-compose -f docker-compose.dev.yml up --build
```

Приложение будет доступно:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## 📁 Структура проекта

```
ai-voice/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   └── ...
│   └── tests/        # Backend tests
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── ...
└── .github/          # CI/CD workflows
```

## 🔧 Development Workflow

### Backend Development

```bash
# Запуск тестов
cd backend
pytest

# Линтинг
flake8 app/

# Создание миграции
make migrate-create MSG="add new table"

# Применение миграций
make migrate
```

### Frontend Development

```bash
# Запуск dev server (вне Docker)
cd frontend
npm install
npm run dev

# Линтинг
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

## 🌿 Git Workflow

### Branching Strategy

- `main` - production-ready code
- `develop` - development branch
- `feature/*` - новые фичи
- `bugfix/*` - исправления багов
- `hotfix/*` - срочные исправления для production

### Commit Messages

Используйте conventional commits:

```
feat: Add user authentication
fix: Resolve database connection issue
docs: Update README with deployment guide
style: Format code with black
refactor: Simplify LLM service logic
test: Add tests for prompt service
chore: Update dependencies
```

### Pull Request Process

1. Создайте feature branch от `develop`:
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

2. Сделайте изменения и commit:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. Push в ваш fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Создайте Pull Request на GitHub:
   - Base: `develop`
   - Compare: `feature/your-feature-name`
   - Заполните описание PR

5. Дождитесь review и прохождения CI checks

## ✅ Code Quality Standards

### Python (Backend)

- Следуйте PEP 8
- Используйте type hints
- Документируйте функции с помощью docstrings
- Покрытие тестами минимум 80%

```python
async def get_user(user_id: str) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        user_id: Unique user identifier

    Returns:
        User object if found, None otherwise
    """
    return await db.query(User).filter(User.id == user_id).first()
```

### TypeScript (Frontend)

- Используйте строгую типизацию
- Следуйте ESLint правилам
- Компоненты должны быть функциональными (React hooks)
- Используйте meaningful имена переменных

```typescript
interface UserProfile {
  id: string;
  name: string;
  email: string;
}

const UserCard: React.FC<{ user: UserProfile }> = ({ user }) => {
  return (
    <div>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
};
```

## 🧪 Testing

### Backend Tests

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный файл
pytest tests/test_chat.py

# С выводом print
pytest -s
```

### Frontend Tests

```bash
cd frontend

# Запуск тестов (когда будут добавлены)
npm run test

# Coverage
npm run test:coverage
```

## 📝 Documentation

- Обновляйте README.md при добавлении новых фич
- Документируйте API endpoints в docstrings
- Добавляйте примеры использования
- Комментируйте сложную логику

## 🐛 Bug Reports

При создании issue о баге включите:

1. **Описание**: Что произошло
2. **Ожидаемое поведение**: Что должно было произойти
3. **Шаги воспроизведения**:
   ```
   1. Перейти на страницу X
   2. Нажать кнопку Y
   3. Увидеть ошибку Z
   ```
4. **Окружение**:
   - OS: Ubuntu 22.04
   - Docker version: 24.0.0
   - Browser: Chrome 120
5. **Логи/Скриншоты**

## 💡 Feature Requests

При предложении новой фичи опишите:

1. **Проблема**: Какую проблему это решит
2. **Решение**: Как вы предлагаете это реализовать
3. **Альтернативы**: Рассматривали ли другие подходы
4. **Use case**: Пример использования

## 🎯 Current Priorities

Фичи, над которыми можно поработать:

### MVP (Фаза 1-3)
- [ ] Backend FastAPI setup
- [ ] LLM интеграция
- [ ] Frontend React app
- [ ] Prompt editor
- [ ] Chat interface

### RAG (Фаза 4)
- [ ] Document upload
- [ ] Vector search
- [ ] RAG integration

### Nice to Have
- [ ] Аутентификация пользователей
- [ ] Rate limiting
- [ ] Metrics dashboard
- [ ] A/B testing промптов

## 📞 Вопросы?

- 💬 Telegram: @your_support
- 📧 Email: dev@your-domain.com
- 🐛 Issues: [GitHub Issues](../../issues)

## 📄 Лицензия

Внося изменения в проект, вы соглашаетесь с тем, что ваш код будет распространяться под лицензией MIT.

---

Спасибо за ваш вклад! 🎉
