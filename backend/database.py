"""
ⒸAngelaMos | 2026
/backend/database.py
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

import asyncpg
from asyncpg import Connection, Pool, Record

import config


logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Manages PostgreSQL connection pool with pgvector support

    Provides methods for executing queries, managing transactions,
    and handling vector operations efficiently
    """
    def __init__(self) -> None:
        """
        Initialize database pool instance
        """
        self._pool: Pool | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Initialize connection pool with pgvector extension
        """
        if self._pool is not None:
            return

        async with self._lock:
            if self._pool is not None:
                return  # type: ignore[unreachable]

            try:
                self._pool = await asyncpg.create_pool(
                    config.settings.database_url,
                    min_size = config.settings.db_pool_min_size,
                    max_size = config.settings.db_pool_max_size,
                    command_timeout = config.settings.db_command_timeout,
                    timeout = config.settings.db_pool_timeout,
                    init = self._init_connection,
                )

                await self._verify_pgvector()

                logger.info(
                    "Database pool created successfully",
                    extra = {
                        "min_size": config.settings.db_pool_min_size,
                        "max_size": config.settings.db_pool_max_size,
                    },
                )

            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise

    async def disconnect(self) -> None:
        """
        Close all connections in the pool
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    async def _init_connection(self, conn: Connection) -> None:
        """
        Initialize individual connection with vector codec
        """
        with suppress(asyncpg.PostgresError, ValueError):
            await conn.set_type_codec(
                "vector",
                encoder = lambda v: f"[{','.join(map(str, v))}]",
                decoder = lambda v: list(map(float, v[1 :-1].split(","))),
                schema = "public",
            )

    async def _verify_pgvector(self) -> None:
        """
        Verify required extensions are installed and create if needed
        Then register vector type codec for all connections
        """
        async with self.acquire() as conn:
            try:
                await conn.execute(
                    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
                )
                logger.info("uuid-ossp extension created successfully")
            except asyncpg.PostgresError as e:
                raise RuntimeError(
                    f"uuid-ossp extension is required but could not be created: {e}"
                ) from e

            result = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
                """
            )

            if not result:
                try:
                    await conn.execute(
                        "CREATE EXTENSION IF NOT EXISTS vector;"
                    )
                    logger.info("pgvector extension created successfully")
                except asyncpg.PostgresError as e:
                    raise RuntimeError(
                        f"pgvector extension is required but could not be created: {e}"
                    ) from e

        await self._register_vector_types()

    async def _register_vector_types(self) -> None:
        """
        Register vector type codec for all connections in the pool
        """
        if self._pool is None:
            return

        async with self.acquire() as conn:
            await conn.set_type_codec(
                "vector",
                encoder = lambda v: f"[{','.join(map(str, v))}]",
                decoder = lambda v: list(map(float, v[1 :-1].split(","))),
                schema = "public",
            )

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Connection]:
        """
        Acquire a connection from the pool
        """
        if self._pool is None:
            raise RuntimeError(
                "Database pool is not initialized. Call connect() first."
            )

        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[Connection]:
        """
        Future: Create a database transaction for atomic multi-step operations
        """
        async with self.acquire() as conn, conn.transaction():
            yield conn

    async def execute(
        self,
        query: str,
        *args: Any,
        timeout: float | None = None
    ) -> str:
        """
        Execute a query without returning results
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout = timeout)  # type: ignore[no-any-return]

    async def executemany(self, query: str, args: list[list[Any]]) -> str:
        """
        Future: Execute a query multiple times with different parameters (bulk insert)
        """
        async with self.acquire() as conn:
            return await conn.executemany(query, args)  # type: ignore[no-any-return]

    async def fetch(
        self,
        query: str,
        *args: Any,
        timeout: float | None = None
    ) -> list[Record]:
        """
        Execute a query and return all results.
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout = timeout)  # type: ignore[no-any-return]

    async def fetchrow(
        self,
        query: str,
        *args: Any,
        timeout: float | None = None
    ) -> Record | None:
        """
        Execute a query and return first result
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout = timeout)

    async def fetchval(
        self,
        query: str,
        *args: Any,
        column: int = 0,
        timeout: float | None = None
    ) -> Any:
        """
        Execute a query and return single value
        """
        async with self.acquire() as conn:
            return await conn.fetchval(
                query,
                *args,
                column = column,
                timeout = timeout
            )

    async def vector_similarity_search(
        self,
        table_name: str,
        embedding_column: str,
        query_embedding: list[float],
        limit: int = config.DEFAULT_PAGE_SIZE,
        filters: dict[str,
                      Any] | None = None,
    ) -> list[Record]:
        """
        Perform vector similarity search using pgvector
        """
        # Build the WHERE clause
        where_conditions = []
        params = [query_embedding]
        param_count = 1

        if filters:
            for key, value in filters.items():
                param_count += 1
                where_conditions.append(f"{key} = ${param_count}")
                params.append(value)

        where_clause = (
            f"WHERE {' AND '.join(where_conditions)}"
            if where_conditions else ""
        )

        query = f"""
            SELECT *,
                   ({embedding_column} <=> $1::vector) as distance,
                   1 - ({embedding_column} <=> $1::vector) as similarity
            FROM {table_name}
            {where_clause}
            ORDER BY {embedding_column} <=> $1::vector
            LIMIT {limit}
        """

        return await self.fetch(query, *params)

    async def create_vector_index(
        self,
        table_name: str,
        embedding_column: str,
        index_type: str = "ivfflat",
        lists: int = config.IVFFLAT_INDEX_LISTS,
    ) -> None:
        """
        Create a vector similarity index for efficient search.
        """
        index_name = f"idx_{table_name}_{embedding_column}_{index_type}"

        if index_type == "ivfflat":
            query = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}
                USING ivfflat ({embedding_column} vector_cosine_ops)
                WITH (lists = {lists})
            """
        elif index_type == "hnsw":
            query = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}
                USING hnsw ({embedding_column} vector_cosine_ops)
            """
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        await self.execute(query)
        logger.info(f"Created vector index {index_name}")

    @property
    def pool(self) -> Pool | None:
        """
        Get the underlying connection pool.
        """
        return self._pool


# Global database instance
db = DatabasePool()


async def init_db() -> None:
    """
    Initialize database connection pool.

    Should be called during application startup
    """
    await db.connect()


async def close_db() -> None:
    """
    Close database connection pool.

    Should be called during application shutdown
    """
    await db.disconnect()
