"""
ⒸAngelaMos | 2026
changelog.py - Changelog schemas
"""

from pydantic import BaseModel


class ChangelogSection(BaseModel):
    """
    Section of changes (Added, Changed, Fixed, etc.)
    """
    added: list[str] = []
    changed: list[str] = []
    deprecated: list[str] = []
    removed: list[str] = []
    fixed: list[str] = []
    security: list[str] = []


class ChangelogVersion(BaseModel):
    """
    Single version entry in changelog
    """
    version: str
    date: str
    changes: ChangelogSection


class ChangelogResponse(BaseModel):
    """
    Complete changelog with all versions
    """
    versions: list[ChangelogVersion]
