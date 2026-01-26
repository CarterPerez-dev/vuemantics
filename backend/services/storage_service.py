"""
ⒸAngelaMos | 2026
storage_service.py
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

import aiofiles
import cv2
from PIL import Image

import config
from core.validators import FileValidator
from core.validators.file import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


logger = logging.getLogger(__name__)


class StorageService:
    """
    Handles file storage operations with cloud-ready interface

    Currently uses local filesystem but designed for easy migration
    to cloud storage services like S3 or Google Cloud Storage
    """
    def __init__(self, base_path: Path | None = None):
        """
        Initialize storage service

        Args:
            base_path: Base directory for uploads (defaults to settings)
        """
        self.base_path = base_path or config.settings.upload_path
        logger.info(
            f"Storage service initialized with base path: {self.base_path}"
        )

    def _get_upload_dir(self, user_id: UUID, upload_id: UUID) -> Path:
        """
        Get directory path for specific upload.

        Structure: base_path/user_id/upload_id/
        """
        return self.base_path / str(user_id) / str(upload_id)

    async def validate_file(
        self,
        filename: str,
        mime_type: str,
        file_size: int
    ) -> tuple[str,
               str]:
        """
        Validate uploaded file using FileValidator.

        Args:
            filename: Original filename
            mime_type: MIME type
            file_size: Size in bytes

        Returns:
            Tuple of (file_type, extension)
        """
        result = FileValidator.validate(filename, mime_type, file_size)
        return result.file_type, result.extension

    async def save_upload(
        self,
        file_content: BinaryIO,
        user_id: UUID,
        upload_id: UUID,
        extension: str,
    ) -> str:
        """
        Save uploaded file to storage

        Args:
            file_content: File content as binary stream
            user_id: User's ID
            upload_id: Upload's ID
            extension: File extension

        Returns:
            Relative path to saved file
        """
        # Create dir structure
        upload_dir = self._get_upload_dir(user_id, upload_id)
        upload_dir.mkdir(parents = True, exist_ok = True)

        # Save original file
        filename = f"original.{extension}"
        file_path = upload_dir / filename

        async with aiofiles.open(file_path, "wb") as f:
            # Read chunks to handle large files
            while chunk := file_content.read(config.FILE_UPLOAD_CHUNK_SIZE
                                             ):
                await f.write(chunk)

        relative_path = file_path.relative_to(self.base_path)
        logger.info(f"Saved upload to: {relative_path}")

        return str(relative_path)

    async def generate_thumbnail(
        self,
        user_id: UUID,
        upload_id: UUID,
        file_type: str,
        extension: str,
    ) -> str | None:
        """
        Generate thumbnail for upload (async).

        Args:
            user_id: User's ID
            upload_id: Upload's ID
            file_type: 'image' or 'video'
            extension: Original file extension

        Returns:
            Relative path to thumbnail or None if generation fails
        """
        try:
            upload_dir = self._get_upload_dir(user_id, upload_id)
            original_path = upload_dir / f"original.{extension}"
            thumb_path = upload_dir / config.THUMBNAIL_FILENAME

            if file_type == "image":
                await self._generate_image_thumbnail(
                    original_path,
                    thumb_path
                )
            else:
                await self._generate_video_thumbnail(
                    original_path,
                    thumb_path
                )

            relative_path = thumb_path.relative_to(self.base_path)
            logger.info(f"Generated thumbnail: {relative_path}")
            return str(relative_path)

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    async def _generate_image_thumbnail(
        self,
        source_path: Path,
        thumb_path: Path
    ) -> None:
        """
        Generate thumbnail for image
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._generate_image_thumbnail_sync,
            source_path,
            thumb_path
        )

    def _generate_image_thumbnail_sync(
        self,
        source_path: Path,
        thumb_path: Path
    ) -> None:
        """
        Synchronous image thumbnail generation
        """
        with Image.open(source_path) as original_img:
            # Convert RGBA to RGB if needed
            if original_img.mode in ("RGBA", "P"):
                rgb_img = Image.new(
                    "RGB",
                    original_img.size,
                    (255,
                     255,
                     255)
                )
                rgb_img.paste(
                    original_img,
                    mask = original_img.split()[-1]
                    if original_img.mode == "RGBA" else None,
                )
                img = rgb_img
            else:
                img = original_img.copy()

            # Thumbnail with aspect ratio preserved
            img.thumbnail(
                config.settings.thumbnail_size,
                Image.Resampling.LANCZOS
            )

            img.save(
                thumb_path,
                "JPEG",
                quality = config.THUMBNAIL_QUALITY,
                optimize = True
            )

    async def _generate_video_thumbnail(
        self,
        source_path: Path,
        thumb_path: Path
    ) -> None:
        """
        Generate thumbnail from video first frame
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._generate_video_thumbnail_sync,
            source_path,
            thumb_path
        )

    def _generate_video_thumbnail_sync(
        self,
        source_path: Path,
        thumb_path: Path
    ) -> None:
        """
        Synchronous video thumbnail generation
        """
        cap = cv2.VideoCapture(str(source_path))
        try:
            ret, frame = cap.read()
            if ret:
                # BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # PIL
                img = Image.fromarray(frame_rgb)

                img.thumbnail(
                    config.settings.thumbnail_size,
                    Image.Resampling.LANCZOS
                )

                img.save(
                    thumb_path,
                    "JPEG",
                    quality = config.THUMBNAIL_QUALITY,
                    optimize = True
                )
        finally:
            cap.release()

    async def extract_video_frames(
        self,
        user_id: UUID,
        upload_id: UUID,
        extension: str,
        max_frames: int = config.MAX_VIDEO_FRAMES
    ) -> list[str]:
        """
        Extract frames from video for AI analysis

        Args:
            user_id: User's ID
            upload_id: Upload's ID
            extension: Video file extension
            max_frames: Maximum frames to extract

        Returns:
            List of paths to extracted frames
        """
        upload_dir = self._get_upload_dir(user_id, upload_id)
        video_path = upload_dir / f"original.{extension}"
        frames_dir = upload_dir / "frames"
        frames_dir.mkdir(exist_ok = True)

        loop = asyncio.get_event_loop()
        frame_paths = await loop.run_in_executor(
            None,
            self._extract_video_frames_sync,
            video_path,
            frames_dir,
            max_frames,
        )

        return [
            str(Path(p).relative_to(self.base_path)) for p in frame_paths
        ]

    def _extract_video_frames_sync(
        self,
        video_path: Path,
        frames_dir: Path,
        max_frames: int
    ) -> list[str]:
        """
        Synchronous video frame extraction
        """
        cap = cv2.VideoCapture(str(video_path))
        frame_paths = []

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 1 fps or less
            interval = max(int(fps), 1)
            frames_to_extract = min(total_frames // interval, max_frames)

            for i in range(frames_to_extract):
                frame_pos = i * interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

                ret, frame = cap.read()
                if ret:
                    # Rotate portrait frames to landscape for model compatibility
                    height, width = frame.shape[: 2]
                    if height > width:
                        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                    # Save frame
                    frame_path = frames_dir / f"frame_{i:04d}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frame_paths.append(str(frame_path))

        finally:
            cap.release()

        return frame_paths

    async def delete_upload(self, user_id: UUID, upload_id: UUID) -> bool:
        """
        Delete all files for an upload

        Args:
            user_id: User's ID
            upload_id: Upload's ID

        Returns:
            True if deleted, False if not found
        """
        upload_dir = self._get_upload_dir(user_id, upload_id)

        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            logger.info(f"Deleted upload directory: {upload_dir}")
            return True

        return False

    def get_file_url(self, relative_path: str) -> str:
        """
        Get URL for serving file

        For local storage, returns path for nginx to serve
        For cloud storage, would return CDN URL

        Args:
            relative_path: Relative path from storage root

        Returns:
            URL to access the file
        """
        # For local storage, nginx serves from /files/
        return f"/files/{relative_path}"

    async def get_upload_metadata(
        self,
        user_id: UUID,
        upload_id: UUID
    ) -> dict | None:
        """
        Get additional metadata for upload.

        Args:
            user_id: User's ID
            upload_id: Upload's ID

        Returns:
            Metadata dict or None if not found
        """
        upload_dir = self._get_upload_dir(user_id, upload_id)

        # Find original file
        for file_path in upload_dir.glob("original.*"):
            # Get file stats
            stats = file_path.stat()

            # Get image/video metadata
            if file_path.suffix.lower() in IMAGE_EXTENSIONS:
                return await self._get_image_metadata(file_path, stats)
            if file_path.suffix.lower() in VIDEO_EXTENSIONS:
                return await self._get_video_metadata(file_path, stats)

        return None

    async def _get_image_metadata(
        self,
        file_path: Path,
        stats: os.stat_result
    ) -> dict:
        """
        Extract image metadata
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_image_metadata_sync,
            file_path,
            stats
        )

    def _get_image_metadata_sync(
        self,
        file_path: Path,
        stats: os.stat_result
    ) -> dict:
        """
        Synchronous image metadata extraction
        """
        with Image.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "file_size_mb": round(stats.st_size / (1024 * 1024),
                                      2),
            }

    async def _get_video_metadata(
        self,
        file_path: Path,
        stats: os.stat_result
    ) -> dict:
        """
        Extract video metadata
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_video_metadata_sync,
            file_path,
            stats
        )

    def _get_video_metadata_sync(
        self,
        file_path: Path,
        stats: os.stat_result
    ) -> dict:
        """
        Synchronous video metadata extraction
        """
        cap = cv2.VideoCapture(str(file_path))
        try:
            # Get codec fourcc and decode to string
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec: str | None = "".join(
                [chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]
            ).strip().lower()

            # Normalize codec names
            if codec in ("hvc1", "hev1"):
                codec = "hevc"
            elif codec in ("avc1", "h264"):
                codec = "h264"
            elif not codec:
                codec = None

            return {
                "width":
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height":
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps":
                cap.get(cv2.CAP_PROP_FPS),
                "frame_count":
                int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration_seconds":
                int(
                    cap.get(cv2.CAP_PROP_FRAME_COUNT) /
                    cap.get(cv2.CAP_PROP_FPS)
                ),
                "file_size_mb":
                round(stats.st_size / (1024 * 1024),
                      2),
                "codec":
                codec,
            }
        finally:
            cap.release()


storage_service = StorageService()
