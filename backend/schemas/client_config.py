"""
ⒸAngelaMos | 2026
client_config.py - Client configuration schemas
"""

from pydantic import BaseModel, ConfigDict, Field


class ClientConfigResponse(BaseModel):
    """
    Client configuration values from backend

    These are the source of truth for frontend configuration,
    ensuring backend and frontend stay in sync
    """
    model_config = ConfigDict(
        extra = "ignore",
        json_schema_extra = {
            "example": {
                "search_default_similarity_threshold": 0.48,
                "similar_uploads_similarity_threshold": 0.5,
                "similar_uploads_default_limit": 30,
                "max_query_length": 500,
                "default_page_size": 50,
                "max_page_size": 100,
                "max_upload_size_mb": 100,
            }
        },
    )

    search_default_similarity_threshold: float = Field(
        description = "Default similarity threshold for search queries"
    )
    similar_uploads_similarity_threshold: float = Field(
        description = "Similarity threshold for 'find similar' feature"
    )
    similar_uploads_default_limit: int = Field(
        description = "Default number of similar uploads to return"
    )
    max_query_length: int = Field(
        description = "Maximum length for search queries"
    )
    default_page_size: int = Field(
        description = "Default pagination page size"
    )
    max_page_size: int = Field(
        description = "Maximum pagination page size"
    )
    max_upload_size_mb: int = Field(
        description = "Maximum upload file size in megabytes"
    )
