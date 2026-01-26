"""
ⒸAngelaMos | 2026
client_config.py
"""

from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field,
)


class ClientConfigResponse(BaseModel):
    """
    Client configuration values from backend
    """
    model_config = ConfigDict(
        extra = "forbid",
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
