# backend/Makefile

.PHONY: help install test lint format clean docker-up docker-down migrate run dev

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '${BLUE}Resume-HitHub Backend${NC}'
	@echo '${GREEN}Available commands:${NC}'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  ${YELLOW}%-15s${NC} %s\n", $$1, $$2 } /^##@/ { printf "\n${BLUE}%s${NC}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install all dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "${GREEN}✓ Dependencies installed${NC}"

dev: ## Run development server with hot reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run: ## Run production server
	uvicorn app.main:app --host 0.0.0.0 --port 8000

##@ Testing

test: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=term-missing

test-watch: ## Run tests in watch mode
	ptw tests/ -- -v

test-specific: ## Run specific test file (usage: make test-specific TEST=test_auth.py)
	pytest tests/$(TEST) -v -s

##@ Code Quality

lint: ## Run all linters
	@echo "${BLUE}Running Black...${NC}"
	black --check app/
	@echo "${BLUE}Running isort...${NC}"
	isort --check-only app/
	@echo "${BLUE}Running flake8...${NC}"
	flake8 app/
	@echo "${GREEN}✓ All linting passed${NC}"

format: ## Format code automatically
	black app/
	isort app/
	@echo "${GREEN}✓ Code formatted${NC}"

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

##@ Database

migrate: ## Run database migrations
	alembic upgrade head

migration: ## Create new migration (usage: make migration MSG="add user table")
	alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback one migration
	alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data)
	alembic downgrade base
	alembic upgrade head
	@echo "${GREEN}✓ Database reset${NC}"

##@ Docker

docker-up: ## Start all services with docker-compose
	docker-compose up -d
	@echo "${GREEN}✓ Services started${NC}"
	@echo "Backend: http://localhost:8000"
	@echo "Flower: http://localhost:5555"

docker-down: ## Stop all services
	docker-compose down
	@echo "${GREEN}✓ Services stopped${NC}"

docker-build: ## Build docker images
	docker-compose build
	@echo "${GREEN}✓ Images built${NC}"

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

docker-clean: ## Clean up docker resources
	docker-compose down -v
	docker system prune -f
	@echo "${GREEN}✓ Docker cleaned${NC}"

##@ Celery

celery-worker: ## Run Celery worker
	celery -A app.core.celery_app worker --loglevel=info

celery-beat: ## Run Celery beat scheduler
	celery -A app.core.celery_app beat --loglevel=info

celery-flower: ## Run Flower (Celery monitoring)
	celery -A app.core.celery_app flower

##@ Utilities

clean: ## Clean cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "${GREEN}✓ Cache cleaned${NC}"

requirements: ## Generate requirements file from current environment
	pip freeze > requirements.txt
	@echo "${GREEN}✓ Requirements updated${NC}"

shell: ## Open Python shell with app context
	python -c "from app.db.session import SessionLocal; from app.db.models import *; db = SessionLocal(); import IPython; IPython.embed()"

check-env: ## Check if required environment variables are set
	@echo "${BLUE}Checking environment variables...${NC}"
	@test -n "$$DATABASE_URL" && echo "${GREEN}✓ DATABASE_URL${NC}" || echo "${RED}✗ DATABASE_URL not set${NC}"
	@test -n "$$REDIS_URL" && echo "${GREEN}✓ REDIS_URL${NC}" || echo "${RED}✗ REDIS_URL not set${NC}"
	@test -n "$$SECRET_KEY" && echo "${GREEN}✓ SECRET_KEY${NC}" || echo "${RED}✗ SECRET_KEY not set${NC}"

##@ Deployment

deploy-staging: ## Deploy to staging (requires setup)
	@echo "${YELLOW}Deploying to staging...${NC}"
	git push origin develop

deploy-prod: ## Deploy to production (requires setup)
	@echo "${RED}Deploying to production...${NC}"
	@echo "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	git push origin main