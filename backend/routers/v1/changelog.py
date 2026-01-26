"""
ⒸAngelaMos | 2026
changelog.py
"""

import re
from pathlib import Path
from functools import lru_cache

from fastapi import APIRouter, Request

from core import limiter
from schemas import (
    ChangelogVersion,
    ChangelogResponse,
    ChangelogSection,
)


router = APIRouter()

CHANGELOG_PATH = Path(
    __file__
).parent.parent.parent.parent / "CHANGELOG.md"


@lru_cache(maxsize = 1)
def parse_changelog() -> ChangelogResponse:
    """
    Parse CHANGELOG.md and return structured data
    """
    if not CHANGELOG_PATH.exists():
        return ChangelogResponse(versions = [])

    content = CHANGELOG_PATH.read_text(encoding = "utf-8")
    versions = []

    # Match version headers: ## [1.0.1] - 2026-01-26
    version_pattern = r"##\s+\[([^\]]+)\]\s+-\s+(\d{4}-\d{2}-\d{2})"
    version_matches = list(re.finditer(version_pattern, content))

    for i, match in enumerate(version_matches):
        version_num = match.group(1)
        date = match.group(2)

        start = match.end()
        end = version_matches[i + 1].start(
        ) if i + 1 < len(version_matches) else len(content)
        version_content = content[start : end]

        changes = ChangelogSection()
        current_section = None
        items: list[str] = []

        for line in version_content.split("\n"):
            line = line.strip()

            if line.startswith("### Added"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "added"
                items = []
            elif line.startswith("### Changed"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "changed"
                items = []
            elif line.startswith("### Deprecated"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "deprecated"
                items = []
            elif line.startswith("### Removed"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "removed"
                items = []
            elif line.startswith("### Fixed"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "fixed"
                items = []
            elif line.startswith("### Security"):
                if current_section and items:
                    setattr(changes, current_section, items)
                current_section = "security"
                items = []

            elif line.startswith("- ") and current_section:
                items.append(line[2 :])

        if current_section and items:
            setattr(changes, current_section, items)

        versions.append(
            ChangelogVersion(
                version = version_num,
                date = date,
                changes = changes,
            )
        )

    return ChangelogResponse(versions = versions)


@router.get(
    "/changelog",
    response_model = ChangelogResponse,
    summary = "Get API changelog",
)
@limiter.limit("10/minute")
async def get_changelog(request: Request) -> ChangelogResponse:
    """
    Retrieve the API changelog
    """
    return parse_changelog()
