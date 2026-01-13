# =============================================================================
# AngelaMos | 2026
# justfile
# =============================================================================

set dotenv-filename := ".env"
set dotenv-load
set export
set shell := ["bash", "-uc"]
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

project := file_name(justfile_directory())
version := `git describe --tags --always 2>/dev/null || echo "dev"`

# =============================================================================
# Default
# =============================================================================

default:
    @just --list --unsorted

# =============================================================================
# Backend Linting
# =============================================================================

[group('lint')]
ruff *ARGS:
    cd backend && ruff check . {{ARGS}}

[group('lint')]
ruff-fix:
    cd backend && ruff check . --fix
    cd backend && ruff format .

[group('lint')]
ruff-format:
    cd backend && ruff format .

[group('lint')]
lint: ruff

# =============================================================================
# Frontend Linting
# =============================================================================

[group('frontend')]
biome *ARGS:
    cd frontend && pnpm biome check . {{ARGS}}

[group('frontend')]
biome-fix:
    cd frontend && pnpm biome check --write .

[group('frontend')]
tsc *ARGS:
    cd frontend && pnpm tsc --noEmit {{ARGS}}

# =============================================================================
# Type Checking
# =============================================================================

[group('types')]
mypy *ARGS:
    cd backend && mypy . {{ARGS}}

[group('types')]
typecheck: mypy

# =============================================================================
# Testing
# =============================================================================

[group('test')]
pytest *ARGS:
    cd backend && pytest tests {{ARGS}}

[group('test')]
test: pytest

[group('test')]
test-cov:
    cd backend && pytest tests --cov=. --cov-report=term-missing --cov-report=html

[group('test')]
test-unit:
    cd backend && pytest tests -m unit

[group('test')]
test-integration:
    cd backend && pytest tests -m integration

# =============================================================================
# CI / Quality
# =============================================================================

[group('ci')]
ci: lint typecheck test

[group('ci')]
check: ruff mypy

# =============================================================================
# Docker Compose (Production)
# =============================================================================

[group('prod')]
up *ARGS:
    docker compose -f infra/prod/docker-compose.yml up {{ARGS}}

[group('prod')]
start *ARGS:
    docker compose -f infra/prod/docker-compose.yml up -d {{ARGS}}

[group('prod')]
down *ARGS:
    docker compose -f infra/prod/docker-compose.yml down {{ARGS}}

[group('prod')]
stop:
    docker compose -f infra/prod/docker-compose.yml stop

[group('prod')]
build *ARGS:
    docker compose -f infra/prod/docker-compose.yml build {{ARGS}}

[group('prod')]
rebuild:
    docker compose -f infra/prod/docker-compose.yml build --no-cache

[group('prod')]
logs *SERVICE:
    docker compose -f infra/prod/docker-compose.yml logs -f {{SERVICE}}

[group('prod')]
ps:
    docker compose -f infra/prod/docker-compose.yml ps

[group('prod')]
shell service='backend':
    docker compose -f infra/prod/docker-compose.yml exec -it {{service}} /bin/bash

# =============================================================================
# Docker Compose (Development)
# =============================================================================

[group('dev')]
dev-up *ARGS:
    docker compose -f infra/dev/docker-compose.yml up {{ARGS}}

[group('dev')]
dev-start *ARGS:
    docker compose -f infra/dev/docker-compose.yml up -d {{ARGS}}

[group('dev')]
dev-down *ARGS:
    docker compose -f infra/dev/docker-compose.yml down {{ARGS}}

[group('dev')]
dev-stop:
    docker compose -f infra/dev/docker-compose.yml stop

[group('dev')]
dev-build *ARGS:
    docker compose -f infra/dev/docker-compose.yml build {{ARGS}}

[group('dev')]
dev-rebuild:
    docker compose -f infra/dev/docker-compose.yml build --no-cache

[group('dev')]
dev-logs *SERVICE:
    docker compose -f infra/dev/docker-compose.yml logs -f {{SERVICE}}

[group('dev')]
dev-ps:
    docker compose -f infra/dev/docker-compose.yml ps

[group('dev')]
dev-shell service='backend':
    docker compose -f infra/dev/docker-compose.yml exec -it {{service}} /bin/bash

# =============================================================================
# Database (Production)
# =============================================================================

[group('db')]
migrate *ARGS:
    docker compose -f infra/prod/docker-compose.yml exec backend alembic upgrade {{ARGS}}

[group('db')]
migration message:
    docker compose -f infra/prod/docker-compose.yml exec backend alembic revision --autogenerate -m "{{message}}"

[group('db')]
rollback:
    docker compose -f infra/prod/docker-compose.yml exec backend alembic downgrade -1

[group('db')]
db-history:
    docker compose -f infra/prod/docker-compose.yml exec backend alembic history --verbose

[group('db')]
db-current:
    docker compose -f infra/prod/docker-compose.yml exec backend alembic current

# =============================================================================
# Database (Development)
# =============================================================================

[group('db-dev')]
dev-migrate *ARGS:
    docker compose -f infra/dev/docker-compose.yml exec backend alembic upgrade {{ARGS}}

[group('db-dev')]
dev-migration message:
    docker compose -f infra/dev/docker-compose.yml exec backend alembic revision --autogenerate -m "{{message}}"

[group('db-dev')]
dev-rollback:
    docker compose -f infra/dev/docker-compose.yml exec backend alembic downgrade -1

# =============================================================================
# Database (Local - no Docker)
# =============================================================================

[group('db-local')]
migrate-local *ARGS:
    cd backend && uv run alembic upgrade {{ARGS}}

[group('db-local')]
migration-local message:
    cd backend && uv run alembic revision --autogenerate -m "{{message}}"

[group('db-local')]
rollback-local:
    cd backend && uv run alembic downgrade -1

[group('db-local')]
db-history-local:
    cd backend && uv run alembic history --verbose

[group('db-local')]
db-current-local:
    cd backend && uv run alembic current

# =============================================================================
# Local Development (no Docker)
# =============================================================================

[group('local')]
run-backend:
    cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

[group('local')]
run-frontend:
    cd frontend && pnpm dev

[group('local')]
sync:
    cd backend && uv sync

[group('local')]
sync-dev:
    cd backend && uv sync --all-extras

# =============================================================================
# Setup
# =============================================================================

[group('setup')]
setup:
    bash setup.sh

[group('setup')]
install-frontend:
    cd frontend && pnpm install

[group('setup')]
install-backend:
    cd backend && uv sync --all-extras

# =============================================================================
# Utilities
# =============================================================================

[group('util')]
info:
    @echo "Project: {{project}}"
    @echo "Version: {{version}}"
    @echo "OS: {{os()}} ({{arch()}})"

[group('util')]
clean:
    -rm -rf backend/.mypy_cache
    -rm -rf backend/.pytest_cache
    -rm -rf backend/.ruff_cache
    -rm -rf backend/htmlcov
    -rm -rf backend/.coverage
    -rm -rf frontend/node_modules/.cache
    @echo "Cache directories cleaned"

[group('util')]
prune:
    docker system prune -a -f
    @echo "Docker system cleaned"

[group('util')]
[confirm("This will delete ALL Docker data including volumes. Continue?")]
nuke:
    -docker compose -f infra/dev/docker-compose.yml down -v
    -docker compose -f infra/prod/docker-compose.yml down -v
    docker system prune -a -v -f
    @echo "Everything nuked"
