"""
ⒸAngelaMos | 2026
Migration: Add hidden column to uploads table

docker exec -it multimodal-backend-dev uv run python -m migrations.add_hidden_column.py
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
    Add hidden column to uploads table.
    """
    logger.info("Starting migration: add hidden column")

    try:
        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS hidden BOOLEAN NOT NULL DEFAULT FALSE;
            """
        )
        logger.info("Added hidden column")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploads_hidden ON uploads(hidden);
            """
        )
        logger.info("Created index for hidden column")

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """
    Remove hidden column.
    """
    logger.info("Starting migration rollback: remove hidden column")

    try:
        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_hidden;"
        )

        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS hidden;"
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
    
