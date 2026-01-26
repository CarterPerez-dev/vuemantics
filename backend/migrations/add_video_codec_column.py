"""
ⒸAngelaMos | 2026
Migration: Add video_codec column to uploads table

docker exec -it vuemantics-dev-backend uv run python -m migrations.add_video_codec_column
"""

import sys
import asyncio
import logging
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

import database


logger = logging.getLogger(__name__)


async def upgrade():
    """
    Add video_codec column to uploads table for storing video codec info.
    """
    logger.info("Starting migration: add video_codec column")

    try:
        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS video_codec VARCHAR(20);
            """
        )
        logger.info("Added video_codec column")

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """
    Remove video_codec column from uploads table.
    """
    logger.info("Starting migration rollback: remove video_codec column")

    try:
        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS video_codec;"
        )

        logger.info("Migration rollback completed successfully")

    except Exception as e:
        logger.error(f"Migration rollback failed: {e}")
        raise


async def main():
    """
    Run migration from command line.
    """
    logging.basicConfig(level = logging.INFO)

    await database.db.connect()
    try:
        await upgrade()
    finally:
        await database.db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
