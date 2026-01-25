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
    cd frontend && pnpm tsc -b {{ARGS}}

# =============================================================================
# Type Checking
# =============================================================================

[group('types')]
mypy *ARGS:
    cd backend && mypy . {{ARGS}}

[group('types')]
typecheck: mypy

# =============================================================================
# CI / Quality
# =============================================================================

[group('ci')]
ci: lint typecheck

[group('ci')]
check: ruff mypy

# =============================================================================
# Docker Compose (Production)
# =============================================================================

[group('prod')]
prod-up *ARGS:
    docker compose -f prod.compose.yml up {{ARGS}}

[group('prod')]
prod-start *ARGS:
    docker compose -f prod.compose.yml up -d {{ARGS}}

[group('prod')]
prod-down *ARGS:
    docker compose -f prod.compose.yml down {{ARGS}}

[group('prod')]
prod-stop:
    docker compose -f prod.compose.yml stop

[group('prod')]
prod-build *ARGS:
    docker compose -f prod.compose.yml build {{ARGS}}

[group('prod')]
prod-rebuild:
    docker compose -f prod.compose.yml build --no-cache

[group('prod')]
prod-logs *SERVICE:
    docker compose -f prod.compose.yml logs -f {{SERVICE}}

[group('prod')]
prod-ps:
    docker compose -f prod.compose.yml ps

[group('prod')]
prod-shell service='backend':
    docker compose -f prod.compose.yml exec -it {{service}} /bin/bash

# =============================================================================
# Docker Compose (Development)
# =============================================================================

[group('dev')]
dev-up *ARGS:
    docker compose -f compose.yml up {{ARGS}}

[group('dev')]
dev-start *ARGS:
    docker compose -f compose.yml up -d {{ARGS}}

[group('dev')]
dev-down *ARGS:
    docker compose -f compose.yml down {{ARGS}}

[group('dev')]
dev-stop:
    docker compose -f compose.yml stop

[group('dev')]
dev-build *ARGS:
    docker compose -f compose.yml build {{ARGS}}

[group('dev')]
dev-rebuild:
    docker compose -f compose.yml build --no-cache

[group('dev')]
dev-logs *SERVICE:
    docker compose -f compose.yml logs -f {{SERVICE}}

[group('dev')]
dev-ps:
    docker compose -f compose.yml ps

[group('dev')]
dev-shell service='backend':
    docker compose -f compose.yml exec -it {{service}} /bin/bash

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
# Setup # TODO
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
    -rm -rf backend/.ruff_cache
    -rm -rf frontend/node_modules/.cache
    @echo "Cache directories cleaned"

[group('util')]
prune:
    docker system prune -a -f
    @echo "Docker system cleaned"

[group('util')]
[confirm("This will delete ALL Docker data including volumes. Continue?")]
nuke:
    -docker compose -f compose.yml down -v
    -docker compose -f prod.compose.yml down -v
    docker system prune -a -v -f
    @echo "Everything nuked"
