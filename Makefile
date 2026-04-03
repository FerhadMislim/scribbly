# ===========================================
# Scribbly - Makefile
# Developer productivity commands
# ===========================================

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Docker Compose command detection
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; fi)
DOCKER_BIN := $(shell command -v docker 2>/dev/null)
HAS_NVIDIA_GPU := $(shell if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then echo "true"; else echo "false"; fi)
HAS_NVIDIA_CONTAINER_TOOLKIT := $(shell if command -v nvidia-ctk >/dev/null 2>&1; then echo "true"; else echo "false"; fi)
DOCKER_GPU_READY := $(if $(filter true,$(HAS_NVIDIA_GPU) $(HAS_NVIDIA_CONTAINER_TOOLKIT)),true,false)
BACKEND_DOCKERFILE ?= $(if $(filter true,$(DOCKER_GPU_READY)),infra/docker/Dockerfile.backend-gpu,infra/docker/Dockerfile.backend-cpu)
CELERY_DOCKERFILE ?= $(if $(filter true,$(DOCKER_GPU_READY)),infra/docker/Dockerfile.celery-gpu,infra/docker/Dockerfile.celery)
GPU_ENABLED ?= $(DOCKER_GPU_READY)
GPU_COUNT ?= $(if $(filter true,$(DOCKER_GPU_READY)),all,)

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
	@echo "  make docker-rebuild   Recreate Docker stack (down, build, up)"
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
.PHONY: compose-check
.PHONY: env-check
compose-check:
	@if [ -z "$(DOCKER_BIN)" ]; then \
		echo "$(YELLOW)Docker is not installed. Install Docker Engine or Docker Desktop first.$(NC)"; \
		exit 1; \
	fi
	@if ! docker info >/dev/null 2>&1; then \
		SOCK_GROUP="$$(stat -c '%G' /var/run/docker.sock 2>/dev/null || true)"; \
		echo "$(YELLOW)Docker is installed, but your user cannot access the Docker daemon.$(NC)"; \
		if [ -n "$$SOCK_GROUP" ] && [ "$$SOCK_GROUP" != "UNKNOWN" ]; then \
			echo "$(YELLOW)Docker socket group: $$SOCK_GROUP$(NC)"; \
			echo "$(YELLOW)If needed, run 'sudo usermod -aG $$SOCK_GROUP $$USER' once, then start a new shell and restart VS Code.$(NC)"; \
		else \
			echo "$(YELLOW)If needed, run 'sudo usermod -aG docker $$USER' once, then start a new shell and restart VS Code.$(NC)"; \
		fi; \
		echo "$(YELLOW)Also verify that VS Code is using the same Docker context and socket as this shell: 'docker context ls' and DOCKER_HOST.$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(DOCKER_COMPOSE)" ]; then \
		echo "$(YELLOW)Docker Compose is not installed. Use Docker Desktop or install either 'docker compose' or 'docker-compose'.$(NC)"; \
		exit 1; \
	fi

env-check:
	@if [ ! -f backend/.env ]; then \
		if [ -f backend/.env.example ]; then \
			cp backend/.env.example backend/.env; \
			echo "$(GREEN)✓ Created backend/.env from backend/.env.example$(NC)"; \
		else \
			echo "$(YELLOW)Missing backend/.env and backend/.env.example$(NC)"; \
			exit 1; \
		fi; \
	fi
	@if [ ! -f web/.env ]; then \
		if [ -f web/.env.example ]; then \
			cp web/.env.example web/.env; \
			echo "$(GREEN)✓ Created web/.env from web/.env.example$(NC)"; \
		else \
			echo "$(YELLOW)Missing web/.env and web/.env.example$(NC)"; \
			exit 1; \
		fi; \
	fi

docker: compose-check env-check
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@echo "$(YELLOW)Backend Dockerfile: $(BACKEND_DOCKERFILE)$(NC)"
	@echo "$(YELLOW)Celery Dockerfile: $(CELERY_DOCKERFILE)$(NC)"
	@echo "$(YELLOW)Host GPU detected: $(HAS_NVIDIA_GPU)$(NC)"
	@echo "$(YELLOW)NVIDIA Container Toolkit installed: $(HAS_NVIDIA_CONTAINER_TOOLKIT)$(NC)"
	@if [ "$(HAS_NVIDIA_GPU)" = "true" ] && [ "$(HAS_NVIDIA_CONTAINER_TOOLKIT)" != "true" ]; then \
		echo "$(YELLOW)GPU hardware is available, but Docker GPU support is not installed.$(NC)"; \
		echo "$(YELLOW)Install NVIDIA Container Toolkit, then rerun 'make docker'.$(NC)"; \
	fi
	@BACKEND_DOCKERFILE=$(BACKEND_DOCKERFILE) CELERY_DOCKERFILE=$(CELERY_DOCKERFILE) GPU_ENABLED=$(GPU_ENABLED) GPU_COUNT=$(GPU_COUNT) $(DOCKER_COMPOSE) up -d
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
docker-build: compose-check
	@echo "$(BLUE)Building Docker images...$(NC)"
	@BACKEND_DOCKERFILE=$(BACKEND_DOCKERFILE) CELERY_DOCKERFILE=$(CELERY_DOCKERFILE) GPU_ENABLED=$(GPU_ENABLED) GPU_COUNT=$(GPU_COUNT) $(DOCKER_COMPOSE) build

.PHONY: docker-down
docker-down: compose-check
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@BACKEND_DOCKERFILE=$(BACKEND_DOCKERFILE) CELERY_DOCKERFILE=$(CELERY_DOCKERFILE) GPU_ENABLED=$(GPU_ENABLED) GPU_COUNT=$(GPU_COUNT) $(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Docker services stopped$(NC)"

.PHONY: docker-rebuild
docker-rebuild: docker-down docker-build docker

.PHONY: docker-logs
docker-logs: compose-check
	@BACKEND_DOCKERFILE=$(BACKEND_DOCKERFILE) CELERY_DOCKERFILE=$(CELERY_DOCKERFILE) GPU_ENABLED=$(GPU_ENABLED) GPU_COUNT=$(GPU_COUNT) $(DOCKER_COMPOSE) logs -f

.PHONY: download-models
download-models:
	@echo "$(BLUE)Downloading AI models...$(NC)"
	@bash ai-engine/scripts/download_models.sh
