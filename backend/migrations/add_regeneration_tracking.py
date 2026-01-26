"""
ⒸAngelaMos | 2026
Migration: Add regeneration tracking fields to uploads table

docker exec -it multimodal-backend-dev uv run python -m migrations.add_regeneration_tracking
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
    Add regeneration_count and last_regenerated_at columns to uploads table.
    """
    logger.info("Starting migration: add regeneration tracking")

    try:
        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS regeneration_count INTEGER NOT NULL DEFAULT 0;
            """
        )
        logger.info("Added regeneration_count column")

        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS last_regenerated_at TIMESTAMP;
            """
        )
        logger.info("Added last_regenerated_at column")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploads_regeneration_count
            ON uploads(regeneration_count)
            WHERE regeneration_count > 0;
            """
        )
        logger.info("Created partial index for regeneration_count")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploads_last_regenerated_at
            ON uploads(last_regenerated_at)
            WHERE last_regenerated_at IS NOT NULL;
            """
        )
        logger.info("Created partial index for last_regenerated_at")

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """
    Remove regeneration tracking columns.
    """
    logger.info(
        "Starting migration rollback: remove regeneration tracking"
    )

    try:
        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_last_regenerated_at;"
        )

        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_regeneration_count;"
        )

        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS last_regenerated_at;"
        )

        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS regeneration_count;"
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
