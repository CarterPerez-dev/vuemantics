# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-26

### Added
- API versioning with `/v1` prefix for future compatibility
- WebSocket support for real-time upload progress updates
- Semantic search powered by pgvector and local AI embeddings
- Local AI integration with Ollama (qwen2.5-vl, bge-m3)
- Automatic thumbnail generation for images
- JWT-based authentication with token rotation
- Background processing for AI-powered image descriptions
- Comprehensive OpenAPI documentation with tag metadata
- Client configuration endpoint for feature flags

### Changed
- Improved token refresh flow to prevent race conditions
- Enhanced error handling with structured exception responses
- Migrated to AGPL-3.0 license
- Updated OpenAPI metadata with contact and license information

### Fixed
- Token expiration handling now proactive (refreshes before expiry)
- WebSocket routes properly unversioned for stability
- CORS configuration for cross-origin requests

## [1.0.0] - 2025-01-25

### Added
- Initial release
- Image upload and storage
- Basic search functionality
- User authentication
- PostgreSQL with pgvector extension
