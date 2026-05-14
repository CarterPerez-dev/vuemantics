"""
ⒸAngelaMos | 2026
transcode_hevc_backfill.py

Backfill: transcode existing HEVC videos to H.264 playback copies.

Run inside container:
docker exec -it vuemantics-dev-backend uv run python -m migrations.transcode_hevc_backfill
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from uuid import UUID

import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_BASE = Path("/storage/uploads")


def detect_hevc(file_path: Path) -> bool:
    cap = cv2.VideoCapture(str(file_path))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join(
        [chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]
    ).strip().lower()
    cap.release()
    return codec in ("hvc1", "hev1", "hevc")


def transcode(original: Path, playback: Path) -> bool:
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(original),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(playback),
        ],
        capture_output=True,
        timeout=600,
    )
    return result.returncode == 0


async def run() -> None:
    import database

    await database.db.connect()

    rows = await database.db.fetch(
        "SELECT id, user_id, file_path FROM uploads WHERE file_type = 'video'"
    )

    logger.info(f"Found {len(rows)} videos to check")

    for row in rows:
        upload_id = row["id"]
        user_id = row["user_id"]
        file_path = row["file_path"]

        upload_dir = STORAGE_BASE / str(user_id) / str(upload_id)
        originals = list(upload_dir.glob("original.*"))
        if not originals:
            logger.warning(f"No original file for {upload_id}")
            continue

        original = originals[0]
        playback = upload_dir / "playback.mp4"

        if playback.exists():
            logger.info(f"Playback already exists for {upload_id}, updating DB path")
            rel = str(playback.relative_to(STORAGE_BASE))
            await database.db.execute(
                "UPDATE uploads SET file_path = $1 WHERE id = $2",
                rel, upload_id,
            )
            continue

        if not detect_hevc(original):
            logger.info(f"{upload_id}: not HEVC, skipping")
            continue

        logger.info(f"Transcoding {upload_id}...")
        success = await asyncio.to_thread(transcode, original, playback)

        if success:
            rel = str(playback.relative_to(STORAGE_BASE))
            await database.db.execute(
                "UPDATE uploads SET file_path = $1, video_codec = 'hevc' WHERE id = $2",
                rel, upload_id,
            )
            logger.info(f"Done: {upload_id} → {rel}")
        else:
            logger.error(f"Failed to transcode {upload_id}")

    await database.db.disconnect()
    logger.info("Backfill complete")


if __name__ == "__main__":
    asyncio.run(run())
