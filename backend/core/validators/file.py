"""
ⒸAngelaMos | 2026
file.py
"""

from dataclasses import dataclass

import config
from core import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)

# SINGLE SOURCE OF TRUTH FOR ALL FILE TYPES
MIME_TO_EXTENSION: dict[str,
                        str] = {
                            "image/jpeg": "jpg",
                            "image/jpg": "jpg",
                            "image/png": "png",
                            "image/webp": "webp",
                            "image/heic": "heic",
                            "image/heif": "heif",
                            "video/mp4": "mp4",
                            "video/quicktime": "mov",
                            "video/x-msvideo": "avi",
                            "video/webm": "webm",
                            "video/mpeg": "mpeg",
                            "video/x-flv": "flv",
                        }

# Derive all other constants from MIME_TO_EXTENSION
ALLOWED_IMAGE_MIMES: set[str] = {
    k
    for k in MIME_TO_EXTENSION
    if k.startswith("image/")
}
ALLOWED_VIDEO_MIMES: set[str] = {
    k
    for k in MIME_TO_EXTENSION
    if k.startswith("video/")
}
ALLOWED_MIME_TYPES: set[str] = set(MIME_TO_EXTENSION.keys())
VALID_EXTENSIONS: set[str] = set(MIME_TO_EXTENSION.values())
IMAGE_EXTENSIONS: set[str] = {
    f".{v}"
    for k, v in MIME_TO_EXTENSION.items()
    if k.startswith("image/")
}
VIDEO_EXTENSIONS: set[str] = {
    f".{v}"
    for k, v in MIME_TO_EXTENSION.items()
    if k.startswith("video/")
}


@dataclass
class FileValidationResult:
    """
    Result of file validation
    """
    file_type: str
    extension: str


class FileValidator:
    """
    Validates uploaded files for size, MIME type, and determines file type
    """
    @classmethod
    def validate(
        cls,
        filename: str,
        mime_type: str,
        file_size: int
    ) -> FileValidationResult:
        """
        Validate uploaded file

        Args:
            filename: Original filename
            mime_type: MIME type
            file_size: Size in bytes

        Returns:
            FileValidationResult with file_type and extension

        Raises:
            FileTooLargeError: If file exceeds size limit
            UnsupportedFileTypeError: If MIME type not allowed
        """
        cls._validate_size(file_size)
        cls._validate_mime_type(mime_type)

        file_type = cls._determine_file_type(mime_type)
        extension = cls._get_extension(filename, mime_type)

        return FileValidationResult(
            file_type = file_type,
            extension = extension
        )

    @classmethod
    def _validate_size(cls, file_size: int) -> None:
        """
        Validate file size is within limits
        """
        if file_size > config.settings.max_upload_size:
            raise FileTooLargeError(
                f"File size {file_size} exceeds limit of "
                f"{config.settings.max_upload_size} bytes"
            )

    @classmethod
    def _validate_mime_type(cls, mime_type: str) -> None:
        """
        Validate MIME type is allowed
        """
        if mime_type not in ALLOWED_MIME_TYPES:
            raise UnsupportedFileTypeError(
                f"MIME type {mime_type} is not supported"
            )

    @classmethod
    def _determine_file_type(cls, mime_type: str) -> str:
        """
        Determine if file is image or video based on MIME type
        """
        if mime_type in ALLOWED_IMAGE_MIMES:
            return "image"
        return "video"

    @classmethod
    def _get_extension(cls, filename: str, mime_type: str) -> str:
        """
        Get file extension from filename or MIME type

        Args:
            filename: Original filename
            mime_type: MIME type

        Returns:
            File extension (without dot)
        """
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
            if ext in VALID_EXTENSIONS:
                return ext

        return MIME_TO_EXTENSION.get(mime_type, "bin")

    @classmethod
    def is_valid_extension(cls, extension: str) -> bool:
        """
        Check if extension is valid
        """
        return extension.lower() in VALID_EXTENSIONS

    @classmethod
    def is_image_mime(cls, mime_type: str) -> bool:
        """
        Check if MIME type is an image
        """
        return mime_type in ALLOWED_IMAGE_MIMES

    @classmethod
    def is_video_mime(cls, mime_type: str) -> bool:
        """
        Check if MIME type is a video
        """
        return mime_type in ALLOWED_VIDEO_MIMES
