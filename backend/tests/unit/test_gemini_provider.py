"""
©AngelaMos | 2026
test_gemini_provider.py
"""

import io
import numpy as np
import pytest
from PIL import Image


def make_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_webp_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


def test_gemini_image_mime_supported():
    from services.ai.providers.gemini import GEMINI_SUPPORTED_IMAGE_MIMES
    assert "image/jpeg" in GEMINI_SUPPORTED_IMAGE_MIMES
    assert "image/png" in GEMINI_SUPPORTED_IMAGE_MIMES
    assert "image/webp" not in GEMINI_SUPPORTED_IMAGE_MIMES


def test_gemini_video_mime_supported():
    from services.ai.providers.gemini import GEMINI_SUPPORTED_VIDEO_MIMES
    assert "video/mp4" in GEMINI_SUPPORTED_VIDEO_MIMES
    assert "video/quicktime" in GEMINI_SUPPORTED_VIDEO_MIMES
    assert "video/x-matroska" not in GEMINI_SUPPORTED_VIDEO_MIMES


def test_normalize_embedding():
    from services.ai.providers.gemini import _normalize
    raw = [3.0, 4.0]
    normed = _normalize(raw)
    norm = np.linalg.norm(normed)
    assert abs(norm - 1.0) < 1e-6


def test_normalize_already_unit():
    from services.ai.providers.gemini import _normalize
    raw = [1.0, 0.0, 0.0]
    normed = _normalize(raw)
    assert abs(normed[0] - 1.0) < 1e-6


def test_normalize_zero_vector():
    from services.ai.providers.gemini import _normalize
    raw = [0.0, 0.0, 0.0]
    result = _normalize(raw)
    assert result == [0.0, 0.0, 0.0]


def test_convert_jpeg_passes_through():
    from services.ai.providers.gemini import _to_gemini_image_bytes
    jpeg = make_jpeg_bytes()
    result_bytes, result_mime = _to_gemini_image_bytes(jpeg, "image/jpeg")
    assert result_mime == "image/jpeg"
    assert result_bytes == jpeg


def test_convert_png_passes_through():
    from services.ai.providers.gemini import _to_gemini_image_bytes
    png = make_png_bytes()
    result_bytes, result_mime = _to_gemini_image_bytes(png, "image/png")
    assert result_mime == "image/png"
    assert result_bytes == png


def test_convert_webp_to_jpeg():
    from services.ai.providers.gemini import _to_gemini_image_bytes
    webp = make_webp_bytes()
    result_bytes, result_mime = _to_gemini_image_bytes(webp, "image/webp")
    assert result_mime == "image/jpeg"
    img = Image.open(io.BytesIO(result_bytes))
    assert img.format == "JPEG"
