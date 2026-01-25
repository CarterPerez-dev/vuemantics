"""
ⒸAngelaMos | 2026
Migration: Add token_version column to users table

docker exec -it multimodal-backend-dev uv run python -m migrations.add_token_version.py
"""

import sys
import logging
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from database import close_db, db, init_db


async def migrate():
    """
    Add token_version column to users table.
    """
    print("Starting migration: add_token_version")

    try:
        await init_db()

        print("Adding token_version column to users table...")
        await db.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 0;
            """
        )

        print("Updating existing users to have token_version = 0...")
        await db.execute(
            """
            UPDATE users
            SET token_version = 0
            WHERE token_version IS NULL;
            """
        )

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(migrate())
