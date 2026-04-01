"""
©AngelaMos | 2026
add_admin_column.py
"""

import asyncio
import logging
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

import database


logger = logging.getLogger(__name__)


async def upgrade():
    logger.info("Starting migration: add is_admin column to users")
    try:
        await database.db.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
        """)
        logger.info("Added is_admin column to users table")
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    logger.info("Rollback: remove is_admin column from users")
    try:
        await database.db.execute(
            "ALTER TABLE users DROP COLUMN IF EXISTS is_admin;"
        )
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
