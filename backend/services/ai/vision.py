"""
ⒸAngelaMos | 2026
vision.py
"""

import asyncio
import base64
import logging
from pathlib import Path

import aiofiles
from starlette import status
import httpx
from ollama import ResponseError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config
from core import VisionError
from services.ai.manager import OllamaManager
from services.ai._preprocess_vision import preprocess_image_for_vision_model
from services.ai.prompts import (
    IMAGE_ANALYSIS_PROMPT,
    VIDEO_FRAME_PROMPT,
    VIDEO_SYNTHESIS_PROMPT,
)


logger = logging.getLogger(__name__)


class VisionService:
    """
    Handles vision analysis using Qwen2.5-VL
    """
    def __init__(
        self,
        ollama: OllamaManager,
        semaphore: asyncio.Semaphore
    ):
        """
        Initialize vision service

        Args:
            ollama: OllamaManager instance
            semaphore: Semaphore for concurrency control
        """
        self._ollama = ollama
        self._semaphore = semaphore

    @retry(
        retry = retry_if_exception_type(
            (httpx.TimeoutException,
             httpx.ConnectError)
        ),
        stop = stop_after_attempt(3),
        wait = wait_exponential(multiplier = 1,
                                min = 2,
                                max = 30),
    )
    async def analyze_image(self, image_path: Path) -> str:
        """
        Analyze image with Qwen2.5-VL via Ollama.

        Args:
            image_path: Path to image file

        Returns:
            Text description of image content
        """
        try:
            async with self._semaphore:
                # Read image
                async with aiofiles.open(image_path, "rb") as f:
                    image_data = await f.read()

                # Preprocess in executor (non-blocking)
                loop = asyncio.get_event_loop()
                preprocessed_data = await loop.run_in_executor(
                    None,
                    preprocess_image_for_vision_model,
                    image_data
                )

                image_b64 = base64.b64encode(preprocessed_data
                                             ).decode("utf-8")

                client = await self._ollama.get_client()
                response = await client.chat(
                    model = config.settings.vision_model,
                    messages = [
                        {
                            "role": "user",
                            "content": IMAGE_ANALYSIS_PROMPT,
                            "images": [image_b64],
                        }
                    ],
                    options = {
                        "temperature": config.OLLAMA_VISION_TEMPERATURE,
                        "num_predict":
                        config.OLLAMA_VISION_NUM_PREDICT_IMAGE,
                        "num_ctx": config.OLLAMA_VISION_NUM_CTX,
                    },
                )

                return response["message"]["content"].strip()  # type: ignore[no-any-return]

        except ResponseError as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                raise VisionError(
                    f"Model not loaded. Run: ollama pull {config.settings.vision_model}"
                ) from e
            raise VisionError(f"Vision model error: {e.error}") from e
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise VisionError(f"Failed to analyze image: {e!s}") from e

    async def _analyze_single_frame(self, frame_path: Path) -> str:
        """
        Analyze a single video frame

        Args:
            frame_path: Path to frame image

        Returns:
            Text description of frame content
        """
        async with aiofiles.open(frame_path, "rb") as f:
            frame_data = await f.read()

        loop = asyncio.get_event_loop()
        preprocessed_frame = await loop.run_in_executor(
            None,
            preprocess_image_for_vision_model,
            frame_data
        )

        frame_b64 = base64.b64encode(preprocessed_frame).decode("utf-8")

        client = await self._ollama.get_client()
        response = await client.chat(
            model = config.settings.vision_model,
            messages = [
                {
                    "role": "user",
                    "content": VIDEO_FRAME_PROMPT,
                    "images": [frame_b64],
                }
            ],
            options = {
                "temperature": config.OLLAMA_VISION_TEMPERATURE,
                "num_predict": config.OLLAMA_VISION_NUM_PREDICT_IMAGE,
                "num_ctx": config.OLLAMA_VISION_NUM_CTX,
            },
        )

        return response["message"]["content"].strip()  # type: ignore[no-any-return]

    async def analyze_video(
        self,
        frame_paths: list[Path],
        max_frames: int = config.MAX_VIDEO_FRAMES_FOR_ANALYSIS
    ) -> str:
        """
        Analyze video by processing frames individually and synthesizing

        Processes each frame separately to avoid qwen2.5vl multi-image bug
        Then combines frame descriptions into cohesive video description

        Args:
            frame_paths: List of paths to extracted frames
            max_frames: Maximum frames to analyze

        Returns:
            Text description of video content
        """
        try:
            async with self._semaphore:
                if not frame_paths:
                    raise VisionError(
                        "No frames provided for video analysis"
                    )

                frames_to_process = frame_paths[: max_frames]
                logger.info(
                    f"Analyzing {len(frames_to_process)} video frames individually"
                )

                # Analyze each frame separately (workaround for qwen2.5vl bug)
                frame_descriptions = []
                for i, frame_path in enumerate(frames_to_process, 1):
                    logger.debug(
                        f"Analyzing frame {i}/{len(frames_to_process)}"
                    )
                    description = await self._analyze_single_frame(
                        frame_path
                    )
                    frame_descriptions.append(f"Frame {i}: {description}")

                # Synthesize frame descriptions into cohesive video description
                synthesis_prompt = VIDEO_SYNTHESIS_PROMPT.format(
                    frame_count = len(frame_descriptions),
                    frame_descriptions = "\n\n".join(frame_descriptions)
                )

                client = await self._ollama.get_client()
                response = await client.chat(
                    model = config.settings.vision_model,
                    messages = [
                        {
                            "role": "user",
                            "content": synthesis_prompt,
                        }
                    ],
                    options = {
                        "temperature": config.OLLAMA_VISION_TEMPERATURE,
                        "num_predict":
                        config.OLLAMA_VISION_NUM_PREDICT_VIDEO,
                        "num_ctx": config.OLLAMA_VISION_NUM_CTX,
                    },
                )

                logger.info("Video analysis completed successfully")
                return response["message"]["content"].strip()  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise VisionError(f"Failed to analyze video: {e!s}") from e
