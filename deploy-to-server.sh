#!/bin/bash

# Automated deployment script for voice.matrixcontrol.ru
# This script will deploy the latest code to the server

SERVER="217.26.27.210"
USER="root"
PROJECT_PATH="/root/ai-voice"

echo "🚀 Deploying AI Voice to $SERVER..."
echo ""

# Execute commands on remote server
ssh $USER@$SERVER << 'ENDSSH'
    set -e

    echo "📂 Navigating to project directory..."
    cd /root/ai-voice

    echo "📥 Pulling latest changes from Git..."
    git pull

    echo "🛑 Stopping containers..."
    docker compose down

    echo "🗑️ Removing old frontend image..."
    docker rmi ai-voice-frontend 2>/dev/null || true

    echo "🏗️ Building frontend with VITE_API_URL=/api..."
    docker compose build --no-cache --build-arg VITE_API_URL=/api frontend

    echo "🚀 Starting all services..."
    docker compose up -d

    echo "⏳ Waiting for services to start..."
    sleep 5

    echo "✅ Checking container status..."
    docker compose ps

    echo ""
    echo "📋 Frontend logs:"
    docker compose logs --tail=15 frontend

    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Check: https://voice.matrixcontrol.ru"
ENDSSH

echo ""
echo "🎉 Done! Open https://voice.matrixcontrol.ru in browser"
echo "   Press F12 and check console for:"
echo "   🔧 API Base URL: /api"
