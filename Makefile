# ===========================================
# Scribbly - Makefile
# Developer productivity commands
# ===========================================

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# ===========================================
# Help
# ===========================================
.PHONY: help
help:
	@echo ""
	@echo "$(BLUE)Scribbly - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup$(NC)"
	@echo "  make setup              Install all dependencies (backend + web)"
	@echo "  make setup-backend     Install backend dependencies only"
	@echo "  make setup-web        Install web dependencies only"
	@echo ""
	@echo "$(GREEN)Development$(NC)"
	@echo "  make dev-backend       Start backend dev server (port 8000)"
	@echo "  make dev-web          Start web dev server (port 3000)"
	@echo "  make dev              Start both backend and web"
	@echo "  make docker           Start all services via Docker Compose"
	@echo ""
	@echo "$(GREEN)Testing$(NC)"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-web        Run web tests"
	@echo "  make lint             Run linting on all code"
	@echo ""
	@echo "$(GREEN)Utilities$(NC)"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-logs     View Docker logs"
	@echo ""
	@echo "$(GREEN)AI Engine$(NC)"
	@echo "  make download-models  Download AI models (requires HuggingFace login)"
	@echo ""

# ===========================================
# Setup
# ===========================================
.PHONY: setup
setup: setup-backend setup-web
	@echo "$(GREEN)✓ All dependencies installed!$(NC)"
	@echo "$(YELLOW)Note:$(NC)"
	@echo "  - Backend uses uv (faster than pip)"
	@echo "  - Run 'source backend/.venv/bin/activate' to activate backend venv"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy environment files:"
	@echo "     cp backend/.env.example backend/.env"
	@echo "  2. Start Docker services: make docker"
	@echo "  3. Start dev servers: make dev"

.PHONY: setup-backend
setup-backend:
	@echo "$(BLUE)Setting up backend with uv (Python 3.13)...$(NC)"
	@cd backend && uv venv .venv --python python3.13
	@cd backend && uv sync
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

.PHONY: setup-web
setup-web:
	@echo "$(BLUE)Setting up web...$(NC)"
	@cd web && npm install
	@echo "$(GREEN)✓ Web dependencies installed$(NC)"

# ===========================================
# Development
# ===========================================
.PHONY: dev-backend
dev-backend:
	@echo "$(BLUE)Starting backend on http://localhost:8000$(NC)"
	@cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

.PHONY: dev-web
dev-web:
	@echo "$(BLUE)Starting web on http://localhost:3000$(NC)"
	@cd web && npm run dev

.PHONY: dev
dev: docker
	@echo "$(BLUE)Starting development servers...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Web: http://localhost:3000$(NC)"
	@echo "$(YELLOW)API Docs: http://localhost:8000/docs$(NC)"
	@make dev-backend & make dev-web

.PHONY: docker
docker:
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Docker services started$(NC)"

# ===========================================
# Testing
# ===========================================
.PHONY: test
test: test-backend test-web
	@echo "$(GREEN)✓ All tests passed!$(NC)"

.PHONY: test-backend
test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	@cd backend && . .venv/bin/activate && pytest --cov=app --cov-report=term-missing

.PHONY: test-web
test-web:
	@echo "$(BLUE)Running web tests...$(NC)"
	@cd web && npm test

.PHONY: lint
lint:
	@echo "$(BLUE)Running linters...$(NC)"
	@cd backend && . .venv/bin/activate && ruff check .
	@cd web && npm run lint

# ===========================================
# Utilities
# ===========================================
.PHONY: clean
clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned!$(NC)"

.PHONY: docker-build
docker-build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build

.PHONY: docker-logs
docker-logs:
	@docker-compose logs -f

.PHONY: download-models
download-models:
	@echo "$(BLUE)Downloading AI models...$(NC)"
	@bash scripts/download_models.sh
