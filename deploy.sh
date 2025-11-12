#!/bin/bash

# AI Voice Hostess Bot - Production Deployment Script
# This script runs on the server to deploy the application

set -e  # Exit on error

echo "=========================================="
echo "🚀 AI Voice Hostess Bot - Deployment"
echo "=========================================="
echo ""

# Configuration
PROJECT_DIR="/root/ai-voice"
REPO_URL="https://github.com/Vovanwotkd/ai-voice.git"
BRANCH="main"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create project directory if it doesn't exist
echo -e "${YELLOW}[1/8]${NC} Checking project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Creating project directory..."
    mkdir -p "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"
echo -e "${GREEN}✓${NC} Project directory ready"
echo ""

# Step 2: Clone or pull repository
echo -e "${YELLOW}[2/8]${NC} Updating code from GitHub..."
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git fetch origin
    git reset --hard origin/$BRANCH
    git clean -fd
else
    echo "Cloning repository..."
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
fi
echo -e "${GREEN}✓${NC} Code updated"
echo ""

# Step 3: Check .env file
echo -e "${YELLOW}[3/8]${NC} Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "❌ IMPORTANT: Edit .env file and add your API keys!"
    echo "Run: nano .env"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file exists"
echo ""

# Step 4: Stop running containers
echo -e "${YELLOW}[4/8]${NC} Stopping existing containers..."
docker-compose -f docker-compose.yml down || echo "No containers to stop"
echo -e "${GREEN}✓${NC} Containers stopped"
echo ""

# Step 5: Pull latest images (if using pre-built)
echo -e "${YELLOW}[5/8]${NC} Pulling Docker images..."
docker-compose -f docker-compose.yml pull || echo "Building from source..."
echo -e "${GREEN}✓${NC} Images ready"
echo ""

# Step 6: Build and start containers
echo -e "${YELLOW}[6/8]${NC} Building and starting containers..."
docker-compose -f docker-compose.yml up -d --build
echo -e "${GREEN}✓${NC} Containers started"
echo ""

# Step 7: Wait for services to be ready
echo -e "${YELLOW}[7/8]${NC} Waiting for services to start..."
sleep 10
echo -e "${GREEN}✓${NC} Services should be ready"
echo ""

# Step 8: Check status
echo -e "${YELLOW}[8/8]${NC} Checking deployment status..."
docker-compose -f docker-compose.yml ps
echo ""

# Health check
echo "Running health check..."
HEALTH_CHECK=$(curl -s http://localhost:8000/api/health || echo "FAILED")
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo -e "${GREEN}✓${NC} Backend is healthy!"
else
    echo "⚠️  Backend health check failed. Check logs:"
    echo "docker-compose -f docker-compose.yml logs backend"
fi
echo ""

# Final message
echo "=========================================="
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo "=========================================="
echo ""
echo "Your application is running on:"
echo "  • Frontend: http://217.26.27.210:3000"
echo "  • Backend API: http://217.26.27.210:8000"
echo "  • API Docs: http://217.26.27.210:8000/docs"
echo ""
echo "Useful commands:"
echo "  • View logs: docker-compose -f docker-compose.yml logs -f"
echo "  • Restart: docker-compose -f docker-compose.yml restart"
echo "  • Stop: docker-compose -f docker-compose.yml down"
echo ""
echo "Next steps:"
echo "  1. Setup Nginx reverse proxy (port 80/443)"
echo "  2. Configure SSL certificate (Let's Encrypt)"
echo "  3. Setup firewall rules"
echo ""
