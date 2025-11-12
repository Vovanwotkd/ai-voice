.PHONY: help dev prod build up down logs clean test migrate

# Default target
help:
	@echo "🤖 AI Voice Hostess Bot - Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment (with hot reload)"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make dev-logs     - View development logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo "  make prod-logs    - View production logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-create MSG='message' - Create new migration"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo "  make lint         - Run linters"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up Docker resources"
	@echo "  make ps           - Show running containers"
	@echo "  make restart      - Restart all services"
	@echo "  make shell-backend  - Open backend container shell"
	@echo "  make shell-frontend - Open frontend container shell"

# ==========================================
# Development Environment
# ==========================================
dev:
	docker-compose -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.dev.yml up --build

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# ==========================================
# Production Environment
# ==========================================
prod:
	docker-compose up -d

prod-build:
	docker-compose up -d --build

prod-down:
	docker-compose down

prod-logs:
	docker-compose logs -f

# ==========================================
# Database
# ==========================================
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Error: Please provide a migration message with MSG='your message'"; \
		exit 1; \
	fi
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-shell:
	docker-compose exec postgres psql -U postgres -d hostess_db

# ==========================================
# Testing
# ==========================================
test: test-backend

test-backend:
	cd backend && pytest --cov=app --cov-report=term-missing

lint:
	cd backend && flake8 app/
	cd frontend && npm run lint

# ==========================================
# Utilities
# ==========================================
clean:
	docker-compose down -v
	docker system prune -f

ps:
	docker-compose ps

restart:
	docker-compose restart

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

# ==========================================
# Installation
# ==========================================
install:
	@echo "📦 Setting up project..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env file with your configuration"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@echo "🏗️  Building Docker images..."
	docker-compose build
	@echo "✅ Installation complete! Run 'make dev' to start"

# ==========================================
# Quick Start
# ==========================================
start: dev
stop: dev-down
