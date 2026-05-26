.PHONY: help up down logs build rebuild test clean ps status

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)BoltChats — Local Development$(NC)"
	@echo "════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ─────────────────────────────────────────────
# Main Commands
# ─────────────────────────────────────────────

up: ## Start all services (detached)
	@echo "$(BLUE)🚀 Starting BoltChats services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Services started!$(NC)"
	@echo ""
	@make status

down: ## Stop all services
	@echo "$(YELLOW)🛑 Stopping BoltChats services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

logs: ## Show logs from all services (Ctrl+C to exit)
	docker-compose logs -f

build: ## Build all Docker images
	@echo "$(BLUE)🏗️  Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Build complete$(NC)"

rebuild: down build up ## Rebuild and restart all services

restart: ## Restart all services
	@echo "$(YELLOW)♻️  Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

# ─────────────────────────────────────────────
# Service-Specific Commands
# ─────────────────────────────────────────────

up-api: ## Start only API service + dependencies
	docker-compose up -d mongodb redis api

up-ws: ## Start only WebSocket service + dependencies
	docker-compose up -d redis ws

up-storage: ## Start only Storage worker + dependencies
	docker-compose up -d mongodb redis storage

up-web: ## Start only Web frontend + dependencies
	docker-compose up -d api ws web

logs-api: ## Show API service logs
	docker-compose logs -f api

logs-ws: ## Show WebSocket service logs
	docker-compose logs -f ws

logs-storage: ## Show Storage worker logs
	docker-compose logs -f storage

logs-web: ## Show Web frontend logs
	docker-compose logs -f web

# ─────────────────────────────────────────────
# Monitoring
# ─────────────────────────────────────────────

up-monitoring: ## Start monitoring stack (Prometheus + Grafana + Loki)
	@echo "$(BLUE)📊 Starting monitoring stack...$(NC)"
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo "$(GREEN)✅ Monitoring started!$(NC)"
	@echo ""
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001 (admin/admin)"
	@echo "Loki:       http://localhost:3100"

down-monitoring: ## Stop monitoring stack
	docker-compose -f docker-compose.monitoring.yml down

logs-monitoring: ## Show monitoring stack logs
	docker-compose -f docker-compose.monitoring.yml logs -f

# ─────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────

dev-api: ## Run API service locally (outside Docker)
	cd services/boltchats-api && make dev

dev-ws: ## Run WebSocket service locally (outside Docker)
	cd services/boltchats-ws && make dev

dev-storage: ## Run Storage worker locally (outside Docker)
	cd services/boltchats-storage && make run

dev-web: ## Run Web frontend locally (outside Docker)
	cd services/boltchats-web && npm run dev

test: ## Run all tests
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@cd services/boltchats-api && make test
	@cd services/boltchats-ws && make test
	@cd services/boltchats-storage && make test
	@echo "$(GREEN)✅ All tests passed$(NC)"

lint: ## Run linters on all services
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@cd services/boltchats-api && make lint
	@cd services/boltchats-ws && make lint
	@cd services/boltchats-storage && make lint
	@cd services/boltchats-web && npm run lint
	@echo "$(GREEN)✅ Linting complete$(NC)"

# ─────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────

db-shell: ## Open MongoDB shell
	docker-compose exec mongodb mongosh -u root -p rootpassword --authenticationDatabase admin boltchats

db-seed: ## Seed database with sample data
	@echo "$(BLUE)🌱 Seeding database...$(NC)"
	docker-compose exec api python -m scripts.seed
	@echo "$(GREEN)✅ Database seeded$(NC)"

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# ─────────────────────────────────────────────
# Status & Info
# ─────────────────────────────────────────────

ps: ## Show running containers
	docker-compose ps

status: ## Show service status with URLs
	@echo "$(BLUE)📦 BoltChats Services$(NC)"
	@echo "════════════════════════════════════════"
	@echo "$(GREEN)API:       $(NC)http://localhost:8000"
	@echo "$(GREEN)WebSocket: $(NC)http://localhost:8001"
	@echo "$(GREEN)Frontend:  $(NC)http://localhost:3000"
	@echo "$(GREEN)MongoDB:   $(NC)mongodb://localhost:27017"
	@echo "$(GREEN)Redis:     $(NC)redis://localhost:6379"
	@echo ""
	@docker-compose ps

health: ## Check health of all services
	@echo "$(BLUE)🏥 Service Health Check$(NC)"
	@echo "════════════════════════════════════════"
	@curl -sf http://localhost:8000/health && echo "$(GREEN)✓ API$(NC)" || echo "$(RED)✗ API$(NC)"
	@curl -sf http://localhost:8001/health && echo "$(GREEN)✓ WebSocket$(NC)" || echo "$(RED)✗ WebSocket$(NC)"
	@curl -sf http://localhost:3000 && echo "$(GREEN)✓ Frontend$(NC)" || echo "$(RED)✗ Frontend$(NC)"

# ─────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────

clean: ## Stop services and remove volumes (⚠️  data will be lost)
	@echo "$(RED)⚠️  This will delete all data. Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	docker-compose down -v
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

prune: ## Remove all unused Docker resources
	@echo "$(YELLOW)🧹 Pruning Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✅ Prune complete$(NC)"

# ─────────────────────────────────────────────
# Default
# ─────────────────────────────────────────────

.DEFAULT_GOAL := help
