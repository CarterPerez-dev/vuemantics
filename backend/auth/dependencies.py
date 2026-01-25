"""
ⒸAngelaMos | 2026
dependencies.py
"""

from uuid import UUID

from fastapi import Depends

from auth import get_current_user
from core import NotFoundError
from models.Upload import Upload
from models.User import User


async def verify_upload_ownership(
    upload_id: UUID,
    current_user: User = Depends(get_current_user),
) -> Upload:
    """
    Verify user owns the upload and return it
    """
    upload = await Upload.find_by_id(upload_id)

    if not upload or upload.user_id != current_user.id:
        raise NotFoundError("Upload not found")

    return upload
