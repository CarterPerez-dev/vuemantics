"""
ⒸAngelaMos | 2026
Migration: Add batch support to uploads table

docker exec -it vuemantics-dev-backend uv run python -m migrations.add_batch_support
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
    Add batch_id column to uploads table for bulk upload support.
    """
    logger.info("Starting migration: add batch support")

    try:
        # Create upload_batches table first (if running migration in isolation)
        await database.db.execute(
            """
            CREATE TABLE IF NOT EXISTS upload_batches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                total_uploads INTEGER NOT NULL DEFAULT 0,
                processed_uploads INTEGER NOT NULL DEFAULT 0,
                successful_uploads INTEGER NOT NULL DEFAULT 0,
                failed_uploads INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE
            );
            """
        )
        logger.info("Ensured upload_batches table exists")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_upload_batches_user_id ON upload_batches(user_id);
            """
        )
        logger.info("Created index for upload_batches.user_id")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_upload_batches_status ON upload_batches(status);
            """
        )
        logger.info("Created index for upload_batches.status")

        # Add batch_id column to uploads table
        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS batch_id UUID REFERENCES upload_batches(id) ON DELETE SET NULL;
            """
        )
        logger.info("Added batch_id column to uploads table")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploads_batch_id ON uploads(batch_id);
            """
        )
        logger.info("Created index for uploads.batch_id")

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """
    Remove batch support from uploads table.
    """
    logger.info("Starting migration rollback: remove batch support")

    try:
        # Remove index
        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_batch_id;"
        )
        logger.info("Dropped index idx_uploads_batch_id")

        # Remove column
        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS batch_id;"
        )
        logger.info("Dropped batch_id column from uploads table")

        # Note: We don't drop upload_batches table in rollback
        # in case there's data we want to preserve

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
