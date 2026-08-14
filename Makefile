.PHONY: help up rebuild up-backend up-frontend rebuild-backend rebuild-frontend down logs ps \
	test test-backend test-frontend lint lint-backend lint-frontend sync-backend migrate

.DEFAULT_GOAL := help

## --- Docker lifecycle ---

up: ## Start backend and frontend without rebuilding
	docker compose up -d

rebuild: ## Rebuild images (e.g. after dependency or Dockerfile changes) and start
	docker compose up -d --build

up-backend: ## Start only the backend, without rebuilding
	docker compose up -d backend

up-frontend: ## Start only the frontend, without rebuilding
	docker compose up -d frontend

rebuild-backend: ## Rebuild and start only the backend
	docker compose up -d --build backend

rebuild-frontend: ## Rebuild and start only the frontend
	docker compose up -d --build frontend

down: ## Stop and remove containers
	docker compose down

logs: ## Follow backend logs (also where the auto-generated access token is printed on first start)
	docker compose logs -f backend

ps: ## Show container status
	docker compose ps

## --- Database ---

migrate: ## Apply pending Alembic migrations by hand (runs automatically on container start otherwise)
	docker compose run --rm backend alembic upgrade head

## --- Testing & linting (run locally, not in Docker) ---

sync-backend: ## Sync the local backend venv with requirements.txt (same install CI uses)
	cd backend && uv pip install -r requirements.txt --override lxml-override.txt

test-backend: ## Run backend tests with coverage (same invocation as CI)
	cd backend && pytest -v --cov=app --cov-report=xml

test-frontend: ## Run frontend tests with coverage (same invocation as CI)
	cd frontend && yarn test:coverage

test: test-backend test-frontend ## Run backend and frontend test suites

lint: lint-backend lint-frontend ## Lint backend and frontend

lint-backend: ## Lint + type-check the backend (ruff check, ruff format --check, mypy)
	cd backend && ruff check . && ruff format --check . && mypy app

lint-frontend: ## Lint + type-check the frontend (eslint, tsc --noEmit)
	cd frontend && yarn lint && yarn typecheck

## --- Help ---

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
