"""
Pytest configuration and shared fixtures.

Provides test database, async support, and common fixtures
for all test modules.
---
/backend/tests/conftest.py
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from uuid import uuid4

import asyncpg
import pytest
import pytest_asyncio
from asyncpg import Connection
from httpx import AsyncClient

# Add backend to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth import hash_password
from config import Settings, get_settings
from main import app
from models import User


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Test-specific settings.
    """
    return Settings(
        environment="testing",
        database_url="postgresql://postgres:devpassword@localhost:5432/multimodal_test",
        redis_url="redis://localhost:6379/1",
        secret_key="test-secret-key-for-testing-only",
        debug=True,
        openai_api_key=os.getenv("TEST_OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("TEST_GEMINI_API_KEY", ""),
    )


class TestDatabaseWrapper:
    """
    Wrapper that makes a test connection behave like the DatabasePool.
    This allows existing model code to work without modification.
    """

    def __init__(self, connection: Connection):
        self.connection = connection

    async def execute(self, query: str, *args, **kwargs):
        return await self.connection.execute(query, *args)

    async def fetch(self, query: str, *args, **kwargs):
        return await self.connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args, **kwargs):
        return await self.connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args, **kwargs):
        return await self.connection.fetchval(query, *args)

    async def vector_similarity_search(
        self,
        table_name: str,
        embedding_column: str,
        query_embedding: list[float],
        limit: int = 10,
        filters: dict | None = None,
    ):
        """
        Perform vector similarity search using pgvector.
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
            f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
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

        return await self.connection.fetch(query, *params)

    async def create_vector_index(
        self,
        table_name: str,
        embedding_column: str,
        index_type: str = "ivfflat",
        lists: int = 100,
    ):
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

        await self.connection.execute(query)


@pytest_asyncio.fixture
async def db_connection(test_settings: Settings) -> AsyncGenerator[Connection, None]:
    """
    Create a fresh database connection for each test.
    This avoids event loop conflicts by creating connections per test.
    """
    # Import here to avoid circular imports
    import database
    import models.Base
    import models.Upload
    import models.User

    conn = await asyncpg.connect(test_settings.database_url)

    try:
        # Ensure extensions exist
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Register vector type codec
        await conn.set_type_codec(
            "vector",
            encoder=lambda v: f"[{','.join(map(str, v))}]",
            decoder=lambda v: list(map(float, v[1:-1].split(","))),
            schema="public",
        )

        # Register JSONB codec
        import json

        await conn.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

        # Store original db instance
        original_db = database.db

        # Create wrapper and override global db
        test_db_wrapper = TestDatabaseWrapper(conn)
        database.db = test_db_wrapper
        models.Base.db = test_db_wrapper
        models.User.db = test_db_wrapper
        models.Upload.db = test_db_wrapper

        yield conn

    finally:
        # Restore original db instance
        database.db = original_db
        models.Base.db = original_db
        models.User.db = original_db
        models.Upload.db = original_db

        await conn.close()


@pytest_asyncio.fixture
async def clean_tables(db_connection: Connection) -> None:
    """
    Clean all tables before each test.
    """
    await db_connection.execute("DROP TABLE IF EXISTS uploads CASCADE")
    await db_connection.execute("DROP TABLE IF EXISTS users CASCADE")

    await db_connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
    """)

    await db_connection.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'video')),
            file_size BIGINT NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            gemini_summary TEXT,
            embedding vector(1536),
            thumbnail_path TEXT,
            error_message TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_uploads_user_id ON uploads(user_id);
        CREATE INDEX IF NOT EXISTS idx_uploads_processing_status ON uploads(processing_status);
        CREATE INDEX IF NOT EXISTS idx_uploads_file_type ON uploads(file_type);
        CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads(created_at DESC);
    """)


@pytest_asyncio.fixture
async def test_user(db_connection: Connection, clean_tables: None) -> User:
    """
    Create a test user.
    """
    email = f"test_{uuid4().hex[:8]}@example.com"
    password_hash = hash_password("TestPass123!")

    record = await db_connection.fetchrow(
        """
        INSERT INTO users (email, password_hash, is_active)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        email,
        password_hash,
        True,
    )

    return User.from_record(record)


@pytest_asyncio.fixture
async def inactive_user(db_connection: Connection, clean_tables: None) -> User:
    """
    Create an inactive test user.
    """
    email = f"inactive_{uuid4().hex[:8]}@example.com"
    password_hash = hash_password("TestPass123!")

    record = await db_connection.fetchrow(
        """
        INSERT INTO users (email, password_hash, is_active)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        email,
        password_hash,
        False,
    )

    return User.from_record(record)


@pytest_asyncio.fixture
async def authenticated_client(
    test_user: User, test_settings: Settings
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an authenticated test client.
    """
    from httpx import ASGITransport

    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/token",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
                "grant_type": "password",
            },
        )

        token_data = response.json()
        client.headers["Authorization"] = f"Bearer {token_data['access_token']}"

        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthenticated_client(
    test_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an unauthenticated test client.
    """
    from httpx import ASGITransport

    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Markers for test organization
def pytest_configure(config):
    """
    Register custom markers.
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_api_keys: mark test as requiring real API keys"
    )


# Test data generators
@pytest.fixture
def make_user_data():
    """
    Factory for creating user test data.
    """

    def _make_user_data(**kwargs):
        data = {
            "email": f"user_{uuid4().hex[:8]}@example.com",
            "password": "ValidPass123!",
        }
        data.update(kwargs)
        return data

    return _make_user_data


@pytest.fixture
def sample_embedding() -> list[float]:
    """
    Generate a sample 1536-dimensional embedding.
    """
    import random

    random.seed(42)  # Reproducible
    return [random.uniform(-1, 1) for _ in range(1536)]


# Async utilities
@pytest.fixture
def async_run():
    """
    Helper to run async functions in sync tests.
    """

    def _run(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    return _run
