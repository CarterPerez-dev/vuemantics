"""
ⒸAngelaMos | 2026
_preprocess_vision.py

Private helper for vision model image preprocessing.
Handles dimension alignment, format optimization, and edge cases.
"""

import io
import logging

from PIL import Image, ImageOps

import config


logger = logging.getLogger(__name__)


def preprocess_image_for_vision_model(image_data: bytes) -> bytes:
    """
    Preprocess image for Qwen2.5-VL vision model.

    Handles:
    - Dimensions that don't align with patch size (causes GGML assertion failures)
    - Images too large for efficient inference
    - Animated images (extracts first frame)
    - EXIF orientation
    - Format optimization

    Strategy:
    - Scale down if > vision_max_image_size (default 1568px)
    - Round dimensions DOWN to nearest multiple of vision_patch_size (28px)
    - Never upscale (don't make small images bigger)
    - Preserve lossless formats (PNG, WebP)
    - Convert to JPEG only if already lossy or unsupported format
    - Extract first frame from animated images

    Args:
        image_data: Original image bytes

    Returns:
        Preprocessed image bytes (same or different format)
    """
    try:
        img: Image.Image = Image.open(io.BytesIO(image_data))

        # Handle animated images - extract first frame
        if hasattr(img, 'is_animated') and img.is_animated:
            logger.info("Extracting first frame from animated image")
            img.seek(0)

        # Apply EXIF orientation if present
        img = ImageOps.exif_transpose(img)

        width, height = img.size
        original_format = img.format
        needs_resize = False

        # Calculate target dimensions
        max_size = config.settings.vision_max_image_size
        patch_size = config.settings.vision_patch_size

        # Scale down if too large (maintain aspect ratio)
        if width > max_size or height > max_size:
            scale = max_size / max(width, height)
            width = int(width * scale)
            height = int(height * scale)
            needs_resize = True

        # Round DOWN to nearest multiple of patch_size
        # Never round UP (don't upscale)
        new_width = (width // patch_size) * patch_size
        new_height = (height // patch_size) * patch_size

        # Ensure minimum size (at least 1 patch)
        new_width = max(new_width, patch_size)
        new_height = max(new_height, patch_size)

        if new_width != width or new_height != height:
            needs_resize = True

        # Resize if needed
        if needs_resize:
            logger.info(
                f"Preprocessing image: {width}x{height} → {new_width}x{new_height} "
                f"(format: {original_format})"
            )
            img = img.resize(
                (new_width,
                 new_height),
                Image.Resampling.LANCZOS
            )

        # Convert to RGB if needed (handles RGBA, P, LA, etc.)
        if img.mode not in ("RGB", "L"):
            if img.mode == "RGBA" or "transparency" in img.info:
                # Create white background for transparency
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask = img.split()[3])
                else:
                    background.paste(img)
                img = background
            else:
                img = img.convert("RGB")

        # Determine output format
        # Keep lossless formats (PNG, WebP) if no resize needed and already lossless
        # Use JPEG for lossy sources or if resized
        output = io.BytesIO()

        if original_format in ("PNG", "WEBP") and not needs_resize:
            # Keep original lossless format
            save_format = original_format
            save_kwargs: dict[str, int | bool] = {}
            if save_format == "PNG":
                save_kwargs = {"optimize": True}
        else:
            # Use JPEG for lossy or resized images
            save_format = "JPEG"
            save_kwargs = {
                "quality": config.settings.vision_jpeg_quality,
                "optimize": True
            }

        img.save(output, format = save_format, **save_kwargs)
        return output.getvalue()

    except Exception as e:
        logger.warning(f"Image preprocessing failed, using original: {e}")
        return image_data
