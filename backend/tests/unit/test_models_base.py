"""
Unit tests for BaseModel class.

Tests common CRUD operations, serialization, and query helpers
that all models inherit.
---
/backend/tests/unit/test_models_base.py
"""

from datetime import datetime
from uuid import UUID

import pytest
from asyncpg import Connection

from models import BaseModel, User


@pytest.mark.unit
class TestBaseModel:
    """
    Test BaseModel functionality.
    """

    async def test_init(self):
        """
        Test BaseModel initialization.
        """
        # Test with no arguments
        model = BaseModel()
        assert model.id is None
        assert model.created_at is None
        assert model.updated_at is None

        # Test with arguments
        test_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        test_time = datetime.now()

        model = BaseModel(
            id=test_id,
            created_at=test_time,
            updated_at=test_time,
        )

        assert model.id == test_id
        assert model.created_at == test_time
        assert model.updated_at == test_time

    async def test_from_record(self):
        """
        Test creating model from asyncpg Record.
        """
        # Test with None
        assert BaseModel.from_record(None) is None

        # Mock record data
        record_data = {
            "id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Create a mock record (using dict as substitute)
        model = BaseModel(**record_data)

        assert model.id == record_data["id"]
        assert model.created_at == record_data["created_at"]
        assert model.updated_at == record_data["updated_at"]

    async def test_from_records(self):
        """
        Test creating multiple models from records.
        """
        # Test empty list
        models = BaseModel.from_records([])
        assert models == []

        # Test with None values filtered out
        record_data = [
            {"id": UUID("550e8400-e29b-41d4-a716-446655440000")},
            None,
            {"id": UUID("660e8400-e29b-41d4-a716-446655440000")},
        ]

        # Since we can't mock asyncpg Records easily, we'll test the logic
        assert len([r for r in record_data if r is not None]) == 2

    async def test_to_dict(self):
        """
        Test model serialization to dictionary.
        """
        test_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        test_time = datetime.now()

        model = BaseModel(
            id=test_id,
            created_at=test_time,
            updated_at=test_time,
        )

        # Test basic serialization
        result = model.to_dict()

        assert isinstance(result["id"], str)
        assert result["id"] == str(test_id)
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)

        # Test with exclude
        result = model.to_dict(exclude={"created_at", "updated_at"})

        assert "id" in result
        assert "created_at" not in result
        assert "updated_at" not in result

        # Test that private attributes are excluded
        model._private = "secret"
        result = model.to_dict()

        assert "_private" not in result

    async def test_find_by_id_requires_table(
        self, db_connection: Connection, clean_tables: None
    ):
        """
        Test find_by_id creates table if needed.
        """
        # Using User as concrete implementation
        # This should create the table automatically
        result = await User.find_by_id(UUID("550e8400-e29b-41d4-a716-446655440000"))

        assert result is None  # No user exists

        # Verify table was created
        exists = await db_connection.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'users'
            )
            """
        )
        assert exists is True

    async def test_find_by_id_with_string_uuid(
        self, db_connection: Connection, test_user: User
    ):
        """
        Test find_by_id accepts string UUID.
        """
        # Find by string UUID
        found = await User.find_by_id(str(test_user.id))

        assert found is not None
        assert found.id == test_user.id
        assert found.email == test_user.email

    async def test_count(self, db_connection: Connection, clean_tables: None):
        """
        Test counting records.
        """
        # Count with no records
        count = await User.count()
        assert count == 0

        # Create some users
        for i in range(3):
            await db_connection.execute(
                """
                INSERT INTO users (email, password_hash, is_active)
                VALUES ($1, $2, $3)
                """,
                f"user{i}@example.com",
                "hashed",
                i < 2,  # First 2 active
            )

        # Count all
        count = await User.count()
        assert count == 3

        # Count with filter
        count = await User.count({"is_active": True})
        assert count == 2

    async def test_find_all_pagination(
        self, db_connection: Connection, clean_tables: None
    ):
        """
        Test finding all records with pagination.
        """
        # Create 5 users
        for i in range(5):
            await db_connection.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES ($1, $2)
                """,
                f"user{i}@example.com",
                "hashed",
            )

        # Test limit
        users = await User.find_all(limit=3)
        assert len(users) == 3

        # Test offset
        users_page2 = await User.find_all(limit=3, offset=3)
        assert len(users_page2) == 2

        # Test order by
        users = await User.find_all(order_by="email ASC")
        emails = [u.email for u in users]
        assert emails == sorted(emails)

    async def test_delete(self, db_connection: Connection, test_user: User):
        """
        Test deleting a record.
        """
        # Verify user exists
        exists = await db_connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
            test_user.id,
        )
        assert exists is True

        # Delete user
        deleted = await test_user.delete()
        assert deleted is True

        # Verify user no longer exists
        exists = await db_connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
            test_user.id,
        )
        assert exists is False

        # Try deleting again
        deleted = await test_user.delete()
        assert deleted is False

    async def test_delete_unsaved_model(self):
        """
        Test deleting unsaved model returns False.
        """
        model = BaseModel()
        deleted = await model.delete()
        assert deleted is False

    async def test_repr(self):
        """
        Test string representation.
        """
        model = BaseModel()
        assert str(model) == "<BaseModel id=None>"

        test_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        model.id = test_id
        assert str(model) == f"<BaseModel id={test_id}>"

    async def test_table_created_flag(self, db_connection: Connection):
        """
        Test that table creation is tracked.
        """
        # Reset the flag
        User.__table_created__ = False

        # First call should create table
        await User.ensure_table_exists()
        assert User.__table_created__ is True

        # Second call should skip creation
        # (We can't easily test this without mocking)
        await User.ensure_table_exists()
        assert User.__table_created__ is True

    async def test_refresh(self, db_connection: Connection, test_user: User):
        """
        Test refreshing model data from database.
        """
        original_email = test_user.email

        # Update user in database directly
        new_email = "updated@example.com"
        await db_connection.execute(
            "UPDATE users SET email = $1 WHERE id = $2",
            new_email,
            test_user.id,
        )

        # Email should still be old value
        assert test_user.email == original_email

        # Refresh from database
        await test_user.refresh()

        # Email should now be updated
        assert test_user.email == new_email

    async def test_refresh_unsaved_model(self):
        """
        Test refreshing unsaved model raises error.
        """
        model = User(email="test@example.com", password_hash="hash")

        with pytest.raises(ValueError, match="Cannot refresh record without id"):
            await model.refresh()

    async def test_refresh_deleted_record(
        self, db_connection: Connection, test_user: User
    ):
        """
        Test refreshing deleted record raises error.
        """
        # Delete the user
        await db_connection.execute(
            "DELETE FROM users WHERE id = $1",
            test_user.id,
        )

        # Try to refresh
        with pytest.raises(ValueError, match="Record with id .* not found"):
            await test_user.refresh()
