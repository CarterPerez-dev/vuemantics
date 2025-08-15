"""
Base model class for all database models.

Provides common fields and CRUD operations for all models.
Uses raw asyncpg for performance with async/await throughout.
---
/backend/models/Base.py
"""

from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from asyncpg import Record

import database

T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """
    Base class for all database models.

    Provides:
    - Common fields: id, created_at, updated_at
    - CRUD operations: create, save, delete
    - Query helpers: find_by_id, find_all
    - Serialization: to_dict, from_record
    """

    __tablename__: str = ""  # Must be overridden by subclasses
    __table_created__: bool = False

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize model instance with field values.
        """
        self.id: UUID | None = kwargs.get("id")
        self.created_at: datetime | None = kwargs.get("created_at")
        self.updated_at: datetime | None = kwargs.get("updated_at")

    @classmethod
    async def create_table(cls) -> None:
        """
        Create the table if it doesn't exist.

        Must be implemented by subclasses with their specific schema.
        """
        raise NotImplementedError("Subclasses must implement create_table()")

    @classmethod
    async def ensure_table_exists(cls) -> None:
        """
        Ensure table exists, create if not.
        """
        if not cls.__table_created__:
            await cls.create_table()
            cls.__table_created__ = True

    @classmethod
    def from_record(cls: type[T], record: Record | None) -> T | None:
        """
        Create model instance from asyncpg Record.
        """
        if record is None:
            return None

        return cls(**dict(record))

    @classmethod
    def from_records(cls: type[T], records: list[Record]) -> list[T]:
        """
        Create multiple model instances from asyncpg Records.
        """
        return [cls.from_record(record) for record in records if record is not None]

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        """
        exclude = exclude or set()

        result = {}
        for key, value in self.__dict__.items():
            if key.startswith("_") or key in exclude:
                continue

            if isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value

        return result

    @classmethod
    async def find_by_id(cls: type[T], id: UUID | str) -> T | None:
        """
        Find a record by ID.
        """
        await cls.ensure_table_exists()

        if isinstance(id, str):
            id = UUID(id)

        query = f"""
            SELECT * FROM {cls.__tablename__}
            WHERE id = $1
        """

        record = await database.db.fetchrow(query, id)
        return cls.from_record(record)

    @classmethod
    async def find_all(
        cls: type[T],
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC",
    ) -> list[T]:
        """
        Find all records with pagination.
        """
        await cls.ensure_table_exists()

        query = f"""
            SELECT * FROM {cls.__tablename__}
            ORDER BY {order_by}
            LIMIT $1 OFFSET $2
        """

        records = await database.db.fetch(query, limit, offset)
        return cls.from_records(records)

    @classmethod
    async def count(cls, filters: dict[str, Any] | None = None) -> int:
        """
        Count records matching filters.
        """
        await cls.ensure_table_exists()

        where_clause = ""
        params = []

        if filters:
            conditions = []
            for i, (key, value) in enumerate(filters.items(), 1):
                conditions.append(f"{key} = ${i}")
                params.append(value)
            where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"""
            SELECT COUNT(*) FROM {cls.__tablename__}
            {where_clause}
        """

        count = await database.db.fetchval(query, *params)
        return count or 0

    async def save(self) -> None:
        """
        Save the current instance to database.
        """
        await self.ensure_table_exists()

        if self.id is None:
            await self._insert()
        else:
            await self._update()

    async def _insert(self) -> None:
        """
        Insert new record.
        """
        raise NotImplementedError("Subclasses must implement _insert()")

    async def _update(self) -> None:
        """
        Update existing record.
        """
        raise NotImplementedError("Subclasses must implement _update()")

    async def delete(self) -> bool:
        """
        Delete this record from database.
        """
        if self.id is None:
            return False

        query = f"""
            DELETE FROM {self.__tablename__}
            WHERE id = $1
            RETURNING id
        """

        result = await database.db.fetchval(query, self.id)
        return result is not None

    async def refresh(self) -> None:
        """
        Refresh instance data from database.
        """
        if self.id is None:
            raise ValueError("Cannot refresh record without id")

        query = f"""
            SELECT * FROM {self.__tablename__}
            WHERE id = $1
        """

        record = await database.db.fetchrow(query, self.id)
        if record is None:
            raise ValueError(f"Record with id {self.id} not found")

        for key, value in dict(record).items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        """
        String representation of model instance.
        """
        return f"<{self.__class__.__name__} id={self.id}>"
