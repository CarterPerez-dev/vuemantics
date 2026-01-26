"""
ⒸAngelaMos | 2026
Rename gemini_summary to description

docker exec -it multimodal-backend-dev uv run python -m migrations.rename_gemini_summary_to_description
"""

import asyncio
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, close_db, db


async def main():
    """
    Rename gemini_summary column to description
    """
    print("Renaming gemini_summary to description...")
    await init_db()

    try:
        check_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'uploads'
            AND column_name = 'gemini_summary'
        """

        result = await db.fetchrow(check_query)

        if not result:
            print(
                "Column 'gemini_summary' does not exist. Checking for 'description'..."
            )

            check_desc = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'uploads'
                AND column_name = 'description'
            """

            desc_exists = await db.fetchrow(check_desc)

            if desc_exists:
                print("Column already renamed to 'description'")
            else:
                print(
                    "Neither 'gemini_summary' nor 'description' column found!"
                )

            return

        rename_query = """
            ALTER TABLE uploads
            RENAME COLUMN gemini_summary TO description
        """

        await db.execute(rename_query)
        print("Successfully renamed gemini_summary to description")

        verify_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'uploads'
            AND column_name = 'description'
        """

        verify = await db.fetchrow(verify_query)

        if verify:
            print("Verified: 'description' column exists")
        else:
            print("Warning: Could not verify column rename")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
