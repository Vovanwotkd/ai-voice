# Rebuild Instructions

## Quick Rebuild (Frontend Only)

Since the changes only affect the frontend build configuration:

```bash
# Stop containers
docker compose down

# Rebuild only frontend (faster)
docker compose build --no-cache frontend

# Start everything
docker compose up -d

# Check logs
docker compose logs -f
```

## Full Rebuild (If Needed)

```bash
# Stop and remove everything
docker compose down -v

# Rebuild all services
docker compose build --no-cache

# Start everything
docker compose up -d

# Check logs
docker compose logs -f backend
docker compose logs -f frontend
```

## Verify Fixes

1. **Prompts Page**: http://localhost:3000/prompts
   - Should load all prompts from database

2. **Chat Page**: http://localhost:3000/chat
   - Text messages should send successfully
   - Voice input should work

3. **Voice Call Page**: http://localhost:3000/voice-call
   - Should connect and handle full conversation
   - Transcription should appear for both user and agent

## Check API Endpoints

```bash
# Test prompts endpoint
curl http://localhost:8000/api/prompts/

# Test health endpoint
curl http://localhost:8000/api/health
```
