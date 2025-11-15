@echo off
REM Complete rebuild script to fix API URL issues (Windows)
REM Run this script to rebuild the frontend with correct configuration

echo Stopping all containers...
docker compose down

echo Removing old frontend image...
docker rmi ai-voice-frontend 2>nul

echo Rebuilding frontend with correct VITE_API_URL=/api...
docker compose build --no-cache --build-arg VITE_API_URL=/api frontend

echo Starting all services...
docker compose up -d

echo Waiting for services to start...
timeout /t 5 /nobreak >nul

echo Checking service status...
docker compose ps

echo.
echo Frontend logs (last 20 lines):
docker compose logs --tail=20 frontend

echo.
echo To check if frontend is working, open: http://localhost:3000
echo Or production: https://voice.matrixcontrol.ru
echo.
echo Check browser console for debug messages:
echo Should see: API Base URL: /api
echo.
echo To follow logs:
echo docker compose logs -f frontend
echo docker compose logs -f backend

pause
