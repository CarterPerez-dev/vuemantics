"""
ⒸAngelaMos | 2026
OpenAPI tag metadata for endpoint grouping and documentation
"""

TAGS_METADATA = [
    {
        "name": "auth",
        "description": (
            "**Authentication and user management**\n\n"
            "Handle user registration, login, token refresh, and session management. "
            "Uses JWT access tokens (30min) and refresh tokens (30 days) with rotation."
        ),
    },
    {
        "name": "uploads",
        "description": (
            "**Upload and manage images**\n\n"
            "Create, retrieve, update, and delete image uploads. "
            "Supports automatic thumbnail generation, AI-powered descriptions, "
            "and vector embeddings for semantic search."
        ),
    },
    {
        "name": "search",
        "description": (
            "**Semantic search across images**\n\n"
            "Natural language queries, similarity search, and search suggestions. "
            "Powered by pgvector and local AI embeddings for privacy-first search."
        ),
    },
    {
        "name": "websocket",
        "description": (
            "**Real-time updates via WebSocket**\n\n"
            "Subscribe to live upload progress, AI processing status, and completion events. "
            "Requires authentication via JWT token after connection."
        ),
    },
    {
        "name": "config",
        "description": (
            "**Client configuration**\n\n"
            "Feature flags, limits, and client-specific settings. "
            "Public endpoint for frontend initialization."
        ),
    },
    {
        "name": "health",
        "description": (
            "**Health checks and system status**\n\n"
            "Monitor database connections, AI service availability, and system health."
        ),
    },
    {
        "name": "system",
        "description": (
            "**System endpoints**\n\n"
            "Root endpoint and general system information."
        ),
    },
]
