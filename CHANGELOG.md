# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-26

### Added
- Initial release of Vuemantics - semantic search for images using local AI
- **Core Features:**
  - Image upload with automatic processing and thumbnail generation
  - AI-powered semantic search using natural language queries
  - Similarity search to find visually/semantically similar images
  - Real-time upload progress via WebSocket
  - JWT authentication with secure token rotation
  - User registration and management

- **AI & Search:**
  - Local AI integration with Ollama (qwen2.5-vl for vision, bge-m3 for embeddings)
  - Automatic image description generation using multimodal vision models
  - Vector embeddings stored in PostgreSQL with pgvector
  - IVFFlat indexing for fast similarity search
  - Description quality auditing with configurable thresholds
  - Search suggestions and batch search support

- **API & Infrastructure:**
  - RESTful API with versioning (`/api/v1`)
  - WebSocket endpoint for real-time updates (unversioned at `/api/ws`)
  - Comprehensive OpenAPI documentation with tag metadata
  - Rate limiting with configurable burst limits
  - CORS support for cross-origin requests
  - Correlation ID middleware for request tracking
  - Structured error handling with custom exception types

- **Authentication & Security:**
  - JWT access tokens (30min expiry) and refresh tokens (30 days)
  - Token family tracking for replay attack detection
  - Device tracking for refresh tokens
  - Proactive token refresh to prevent expiration errors
  - Password strength validation
  - Bcrypt hashing with 14 rounds

- **Data Management:**
  - PostgreSQL with asyncpg for async database operations
  - SQLAlchemy 2.0 for ORM
  - Alembic migrations
  - Pagination support for list endpoints
  - Bulk operations (delete, hide/unhide)
  - Upload statistics and metadata tracking

- **Processing & Performance:**
  - Background AI processing queue
  - Concurrent request limiting with semaphores
  - Redis integration for caching and session management
  - Configurable timeouts and retry logic
  - Video frame extraction and analysis

- **Frontend:**
  - React with TypeScript
  - Vite for development and building
  - TanStack Query for data fetching and caching
  - Zustand for state management
  - React Router for navigation
  - SCSS modules for styling

- **DevOps:**
  - Docker Compose for local development
  - Nginx reverse proxy with WebSocket support
  - Environment-based configuration
  - Health check endpoints
  - Production-ready logging

### Technical Stack
- **Backend:** FastAPI, Python 3.13+, PostgreSQL 16+, Redis
- **AI:** Ollama (qwen2.5-vl, bge-m3)
- **Frontend:** React, TypeScript, Vite
- **Infrastructure:** Docker, Nginx, pgvector

### License
- AGPL-3.0
