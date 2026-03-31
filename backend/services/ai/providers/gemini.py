"""
©AngelaMos | 2026
gemini.py
"""

import asyncio
import io
import logging
from datetime import datetime

import numpy as np
from google import genai
from google.genai import types
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from core.websocket import (
    ProcessingStage,
    UploadCompleted,
    UploadFailed,
    UploadProgressPayload,
    UploadProgressUpdate,
    get_publisher,
)
from models.Upload import ProcessingStatus, Upload

logger = logging.getLogger(__name__)

GEMINI_SUPPORTED_IMAGE_MIMES = frozenset({"image/jpeg", "image/png"})
GEMINI_SUPPORTED_VIDEO_MIMES = frozenset({"video/mp4", "video/quicktime"})

_UNSUPPORTED_VIDEO_MSG = (
    "Format not supported by Gemini provider. Re-upload as MP4 or MOV."
)
_VIDEO_TOO_LONG_MSG = "Video exceeds Gemini 120s limit. Re-upload a shorter clip."


def _normalize(values: list[float]) -> list[float]:
    arr = np.array(values, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm == 0:
        return values
    return (arr / norm).tolist()


def _to_gemini_image_bytes(raw: bytes, mime_type: str) -> tuple[bytes, str]:
    if mime_type in GEMINI_SUPPORTED_IMAGE_MIMES:
        return raw, mime_type
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue(), "image/jpeg"


class GeminiProvider:
    """
    AIProvider using Gemini Embedding 2 Preview for direct multimodal embedding.
    No vision description step — embeds raw image/video bytes directly.
    """
    provider_name = "gemini"

    def __init__(self) -> None:
        api_key = config.settings.gemini_api_key
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Cannot use Gemini provider."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = config.settings.gemini_embedding_model
        self._dims = config.settings.gemini_embedding_dimensions
        logger.info(
            f"GeminiProvider initialized (model={self._model}, dims={self._dims})"
        )

    async def _publish_progress(
        self,
        upload_id,
        status: ProcessingStatus,
        stage: ProcessingStage,
        percent: int,
        message: str,
        error_message: str | None = None,
    ) -> None:
        try:
            publisher = get_publisher()
            msg = UploadProgressUpdate(
                payload=UploadProgressPayload(
                    upload_id=str(upload_id),
                    status=status,
                    stage=stage,
                    progress_percent=percent,
                    message=message,
                    error_message=error_message,
                    description_audit_score=None,
                ),
                timestamp=datetime.utcnow(),
            )
            await publisher.publish_progress(str(upload_id), msg)
        except Exception as e:
            logger.warning(f"Failed to publish progress for {upload_id}: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _embed_bytes(
        self, raw_bytes: bytes, mime_type: str, task_type: str
    ) -> list[float]:
        part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
        result = await asyncio.to_thread(
            self._client.models.embed_content,
            model=self._model,
            contents=[part],
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self._dims,
            ),
        )
        raw = list(result.embeddings[0].values)
        return _normalize(raw)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _embed_text(self, text: str, task_type: str) -> list[float]:
        result = await asyncio.to_thread(
            self._client.models.embed_content,
            model=self._model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self._dims,
            ),
        )
        raw = list(result.embeddings[0].values)
        return _normalize(raw)

    async def process_upload(self, upload: Upload) -> None:
        upload_id = upload.id
        file_path = config.settings.upload_path / upload.file_path

        try:
            await upload.update_status(ProcessingStatus.EMBEDDING)
            await self._publish_progress(
                upload_id,
                ProcessingStatus.EMBEDDING,
                ProcessingStage.EMBEDDING_GENERATION,
                10,
                "Reading file for Gemini embedding",
            )

            raw_bytes = await asyncio.to_thread(file_path.read_bytes)

            if upload.file_type == "image":
                embed_bytes, embed_mime = _to_gemini_image_bytes(
                    raw_bytes, upload.mime_type
                )
            else:
                if upload.mime_type not in GEMINI_SUPPORTED_VIDEO_MIMES:
                    raise ValueError(_UNSUPPORTED_VIDEO_MSG)
                embed_bytes, embed_mime = raw_bytes, upload.mime_type

            await self._publish_progress(
                upload_id,
                ProcessingStatus.EMBEDDING,
                ProcessingStage.EMBEDDING_GENERATION,
                40,
                "Sending to Gemini Embedding API",
            )

            embedding = await self._embed_bytes(
                embed_bytes, embed_mime, "RETRIEVAL_DOCUMENT"
            )

            await self._publish_progress(
                upload_id,
                ProcessingStatus.EMBEDDING,
                ProcessingStage.INDEXING,
                85,
                "Saving embedding to database",
            )

            await upload.update_gemini_embedding(embedding)

            completed_msg = UploadCompleted(
                upload_id=str(upload_id),
                description=None,
                audit_score=None,
                timestamp=datetime.utcnow(),
            )
            await get_publisher().publish_progress(str(upload_id), completed_msg)
            logger.info(f"Gemini embedding completed for {upload_id}")

        except Exception as e:
            logger.error(f"Gemini processing failed for {upload_id}: {e}")
            await upload.update_status(
                ProcessingStatus.FAILED,
                error_message=f"Gemini processing failed: {str(e)[:500]}",
            )
            failed_msg = UploadFailed(
                upload_id=str(upload_id),
                error_message=str(e)[:500],
                timestamp=datetime.utcnow(),
            )
            await get_publisher().publish_progress(str(upload_id), failed_msg)

    async def generate_query_embedding(self, query: str) -> list[float]:
        return await self._embed_text(query, "RETRIEVAL_QUERY")


_instance: GeminiProvider | None = None


def get_gemini_provider() -> GeminiProvider:
    global _instance
    if _instance is None:
        _instance = GeminiProvider()
    return _instance
