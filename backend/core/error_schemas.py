"""
ⒸAngelaMos | 2026
Error response schemas for API responses.
"""

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """
    Standard error response format.
    """
    model_config = ConfigDict(extra = "forbid")

    detail: str = Field(description = "Human readable error message")
    type: str = Field(description = "Exception class name")
