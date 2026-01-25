"""
ⒸAngelaMos | 2026

This migration adds the embedding column for local AI models
---
docker exec -it multimodal-backend-dev uv run python -m migrations.add_local_embedding_column.py
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database


logger = logging.getLogger(__name__)


async def upgrade():
    """
    Add local_embedding column for bge-m3 embeddings (1024 dimensions)
    """
    logger.info("Starting migration: add local_embedding column")

    try:
        await database.db.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        await database.db.execute(
            """
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS embedding_local vector(1024);
            """
        )

        logger.info("Added embedding_local column (vector 1024)")

        await database.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_uploads_embedding_local
            ON uploads USING hnsw (embedding_local vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """
        )

        logger.info("Created HNSW index for embedding_local")
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """
    Remove local_embedding column
    """
    logger.info(
        "Starting migration rollback: remove local_embedding column"
    )

    try:
        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_embedding_local;"
        )

        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS embedding_local;"
        )

        logger.info("Migration rollback completed successfully")

    except Exception as e:
        logger.error(f"Migration rollback failed: {e}")
        raise


async def main():
    """
    Run migration from command line
    """
    logging.basicConfig(level = logging.INFO)

    await database.db.connect()
    try:
        await upgrade()
    finally:
        await database.db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
