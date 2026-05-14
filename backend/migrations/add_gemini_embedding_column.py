"""
©AngelaMos | 2026
add_gemini_embedding_column.py
"""

import asyncio
import logging
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

import database


logger = logging.getLogger(__name__)


async def upgrade():
    logger.info("Starting migration: add gemini embedding column + system_settings")
    try:
        await database.db.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        await database.db.execute("""
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS embedding_gemini vector(1536);
        """)
        logger.info("Added embedding_gemini column (vector 1536)")

        await database.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploads_embedding_gemini
            ON uploads USING hnsw (embedding_gemini vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)
        logger.info("Created HNSW index for embedding_gemini")

        await database.db.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await database.db.execute("""
            INSERT INTO system_settings (key, value)
            VALUES ('embedding_provider', 'local')
            ON CONFLICT (key) DO NOTHING;
        """)
        logger.info("Created system_settings table with default provider=local")
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    logger.info("Rollback: remove gemini embedding column + system_settings")
    try:
        await database.db.execute(
            "DROP INDEX IF EXISTS idx_uploads_embedding_gemini;"
        )
        await database.db.execute(
            "ALTER TABLE uploads DROP COLUMN IF EXISTS embedding_gemini;"
        )
        await database.db.execute("DROP TABLE IF EXISTS system_settings;")
        logger.info("Rollback completed")
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise


async def main():
    logging.basicConfig(level=logging.INFO)
    await database.db.connect()
    try:
        await upgrade()
    finally:
        await database.db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
