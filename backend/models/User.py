"""
User model for authentication and user management.

Handles user registration, login, and profile management.
Password hashing is delegated to auth.password module.
---
/backend/models/User.py
"""

from typing import Any

from asyncpg import UniqueViolationError

import database
from models import BaseModel


class User(BaseModel):
    """
    User model for authentication.

    Attributes:
        id: Unique identifier (UUID)
        email: Unique email address
        password_hash: Bcrypt hashed password
        is_active: Whether user account is active
        created_at: Timestamp of account creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "users"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize user instance.
        """
        super().__init__(**kwargs)
        self.email: str = kwargs.get("email", "")
        self.password_hash: str = kwargs.get("password_hash", "")
        self.is_active: bool = kwargs.get("is_active", True)

    @classmethod
    async def create_table(cls) -> None:
        """
        Create users table with indexes.
        """
        query = """
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
        """

        await database.db.execute(query)

    @classmethod
    async def create(
        cls, email: str, password_hash: str, is_active: bool = True
    ) -> "User":
        """
        Create a new user.
        """
        await cls.ensure_table_exists()

        query = """
            INSERT INTO users (email, password_hash, is_active)
            VALUES ($1, $2, $3)
            RETURNING *
        """

        try:
            record = await database.db.fetchrow(
                query, email.lower(), password_hash, is_active
            )
            return cls.from_record(record)
        except UniqueViolationError as e:
            raise ValueError(f"User with email {email} already exists") from e

    @classmethod
    async def find_by_email(cls, email: str) -> "User | None":
        """
        Find user by email address.
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM users
            WHERE LOWER(email) = LOWER($1)
        """

        record = await database.db.fetchrow(query, email)
        return cls.from_record(record)

    @classmethod
    async def find_active_by_email(cls, email: str) -> "User | None":
        """
        Find active user by email address.
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM users
            WHERE LOWER(email) = LOWER($1) AND is_active = TRUE
        """

        record = await database.db.fetchrow(query, email)
        return cls.from_record(record)

    @classmethod
    async def get_all_active(cls, limit: int = 100, offset: int = 0) -> list["User"]:
        """
        Get all active users with pagination.
        """
        await cls.ensure_table_exists()

        query = """
            SELECT * FROM users
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """

        records = await database.db.fetch(query, limit, offset)
        return cls.from_records(records)

    async def _insert(self) -> None:
        """
        Insert new user record.
        """
        query = """
            INSERT INTO users (email, password_hash, is_active)
            VALUES ($1, $2, $3)
            RETURNING *
        """

        record = await database.db.fetchrow(
            query, self.email.lower(), self.password_hash, self.is_active
        )

        for key, value in dict(record).items():
            setattr(self, key, value)

    async def _update(self) -> None:
        """
        Update existing user record.
        """
        query = """
            UPDATE users
            SET email = $1,
                password_hash = $2,
                is_active = $3,
                updated_at = NOW()
            WHERE id = $4
            RETURNING *
        """

        record = await database.db.fetchrow(
            query, self.email.lower(), self.password_hash, self.is_active, self.id
        )

        if record:
            for key, value in dict(record).items():
                setattr(self, key, value)

    async def update_password(self, new_password_hash: str) -> None:
        """
        Update user's password.
        """
        if self.id is None:
            raise ValueError("Cannot update password for unsaved user")

        query = """
            UPDATE users
            SET password_hash = $1,
                updated_at = NOW()
            WHERE id = $2
            RETURNING updated_at
        """

        updated_at = await database.db.fetchval(query, new_password_hash, self.id)
        if updated_at:
            self.password_hash = new_password_hash
            self.updated_at = updated_at

    async def deactivate(self) -> None:
        """
        Deactivate user account.
        """
        if self.id is None:
            raise ValueError("Cannot deactivate unsaved user")

        query = """
            UPDATE users
            SET is_active = FALSE,
                updated_at = NOW()
            WHERE id = $1
            RETURNING updated_at
        """

        updated_at = await database.db.fetchval(query, self.id)
        if updated_at:
            self.is_active = False
            self.updated_at = updated_at

    async def reactivate(self) -> None:
        """
        Reactivate user account.
        """
        if self.id is None:
            raise ValueError("Cannot reactivate unsaved user")

        query = """
            UPDATE users
            SET is_active = TRUE,
                updated_at = NOW()
            WHERE id = $1
            RETURNING updated_at
        """

        updated_at = await database.db.fetchval(query, self.id)
        if updated_at:
            self.is_active = True
            self.updated_at = updated_at

    @classmethod
    async def email_exists(cls, email: str) -> bool:
        """
        Check if email already exists.
        """
        await cls.ensure_table_exists()

        query = """
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE LOWER(email) = LOWER($1)
            )
        """

        return await database.db.fetchval(query, email)

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert to dictionary, excluding password_hash by default.
        """
        if exclude is None:
            exclude = {"password_hash"}
        else:
            # If exclude is explicitly provided (even if empty), respect it
            # Only add password_hash if exclude is None (default behavior)
            pass
        return super().to_dict(exclude)

    def __repr__(self) -> str:
        """
        String representation of User.
        """
        return f"<User id={self.id} email={self.email}>"
