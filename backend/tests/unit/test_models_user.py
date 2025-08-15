"""
Unit tests for User model.

Tests user-specific functionality including authentication,
email handling, and account management.
---
/backend/tests/unit/test_models_user.py
"""

from uuid import UUID, uuid4

import pytest
from asyncpg import Connection

from auth import hash_password, verify_password
from models import User


@pytest.mark.unit
class TestUserModel:
    """
    Test User model functionality.
    """

    async def test_user_init(self):
        """
        Test User initialization.
        """
        user = User()
        assert user.email == ""
        assert user.password_hash == ""
        assert user.is_active is True

        # With arguments
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=False,
        )
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed"
        assert user.is_active is False

    async def test_create_user(self, db_connection: Connection, clean_tables: None):
        """
        Test creating a new user.
        """
        email = "newuser@example.com"
        password_hash = hash_password("ValidPass123!")

        user = await User.create(
            email=email,
            password_hash=password_hash,
            is_active=True,
        )

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == email.lower()  # Should be lowercased
        assert user.password_hash == password_hash
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_create_user_email_case_insensitive(
        self, db_connection: Connection, clean_tables: None
    ):
        """
        Test email is stored lowercase.
        """
        email = "TestUser@EXAMPLE.COM"
        password_hash = hash_password("ValidPass123!")

        user = await User.create(
            email=email,
            password_hash=password_hash,
        )

        assert user.email == "testuser@example.com"

    async def test_create_duplicate_user(
        self, db_connection: Connection, test_user: User
    ):
        """
        Test creating duplicate user raises error.
        """
        with pytest.raises(ValueError, match="already exists"):
            await User.create(
                email=test_user.email,
                password_hash="anotherhash",
            )

        # Also test case-insensitive duplicate
        with pytest.raises(ValueError, match="already exists"):
            await User.create(
                email=test_user.email.upper(),
                password_hash="anotherhash",
            )

    async def test_find_by_email(self, db_connection: Connection, test_user: User):
        """
        Test finding user by email.
        """
        # Find existing user
        found = await User.find_by_email(test_user.email)
        assert found is not None
        assert found.id == test_user.id
        assert found.email == test_user.email

        # Test case-insensitive search
        found = await User.find_by_email(test_user.email.upper())
        assert found is not None
        assert found.id == test_user.id

        # Test non-existent user
        found = await User.find_by_email("nonexistent@example.com")
        assert found is None

    async def test_find_active_by_email(
        self, db_connection: Connection, test_user: User, inactive_user: User
    ):
        """
        Test finding only active users by email.
        """
        # Find active user
        found = await User.find_active_by_email(test_user.email)
        assert found is not None
        assert found.id == test_user.id
        assert found.is_active is True

        # Try to find inactive user
        found = await User.find_active_by_email(inactive_user.email)
        assert found is None

    async def test_get_all_active(self, db_connection: Connection, clean_tables: None):
        """
        Test getting all active users.
        """
        # Create mix of active and inactive users
        for i in range(5):
            await db_connection.execute(
                """
                INSERT INTO users (email, password_hash, is_active)
                VALUES ($1, $2, $3)
                """,
                f"user{i}@example.com",
                "hashed",
                i < 3,  # First 3 are active
            )

        # Get active users
        users = await User.get_all_active(limit=10)
        assert len(users) == 3
        assert all(u.is_active for u in users)

        # Test pagination
        users = await User.get_all_active(limit=2)
        assert len(users) == 2

        users_page2 = await User.get_all_active(limit=2, offset=2)
        assert len(users_page2) == 1

    async def test_email_exists(self, db_connection: Connection, test_user: User):
        """
        Test checking if email exists.
        """
        # Existing email
        exists = await User.email_exists(test_user.email)
        assert exists is True

        # Case-insensitive check
        exists = await User.email_exists(test_user.email.upper())
        assert exists is True

        # Non-existent email
        exists = await User.email_exists("nonexistent@example.com")
        assert exists is False

    async def test_update_password(self, db_connection: Connection, test_user: User):
        """
        Test updating user password.
        """
        old_hash = test_user.password_hash
        new_hash = hash_password("NewPass456!")

        await test_user.update_password(new_hash)

        assert test_user.password_hash == new_hash
        assert test_user.password_hash != old_hash
        assert test_user.updated_at is not None

        # Verify in database
        db_hash = await db_connection.fetchval(
            "SELECT password_hash FROM users WHERE id = $1",
            test_user.id,
        )
        assert db_hash == new_hash

    async def test_update_password_unsaved_user(self):
        """
        Test updating password on unsaved user raises error.
        """
        user = User(email="test@example.com", password_hash="hash")

        with pytest.raises(ValueError, match="Cannot update password for unsaved user"):
            await user.update_password("newhash")

    async def test_deactivate_user(self, db_connection: Connection, test_user: User):
        """
        Test deactivating user account.
        """
        assert test_user.is_active is True

        await test_user.deactivate()

        assert test_user.is_active is False
        assert test_user.updated_at is not None

        # Verify in database
        is_active = await db_connection.fetchval(
            "SELECT is_active FROM users WHERE id = $1",
            test_user.id,
        )
        assert is_active is False

    async def test_reactivate_user(
        self, db_connection: Connection, inactive_user: User
    ):
        """
        Test reactivating user account.
        """
        assert inactive_user.is_active is False

        await inactive_user.reactivate()

        assert inactive_user.is_active is True
        assert inactive_user.updated_at is not None

        # Verify in database
        is_active = await db_connection.fetchval(
            "SELECT is_active FROM users WHERE id = $1",
            inactive_user.id,
        )
        assert is_active is True

    async def test_to_dict_excludes_password(self):
        """
        Test password_hash is excluded from serialization.
        """
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="supersecret",
            is_active=True,
        )

        result = user.to_dict()

        assert "email" in result
        assert "is_active" in result
        assert "password_hash" not in result

        # Can still explicitly include if needed (though not recommended)
        result = user.to_dict(exclude=set())
        assert "password_hash" in result

    async def test_save_new_user(self, db_connection: Connection, clean_tables: None):
        """
        Test saving a new user.
        """
        user = User(
            email="savetest@example.com",
            password_hash=hash_password("ValidPass123!"),
            is_active=True,
        )

        assert user.id is None

        await user.save()

        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

        # Verify in database
        found = await db_connection.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user.id,
        )
        assert found is not None
        assert found["email"] == "savetest@example.com"

    async def test_save_existing_user(self, db_connection: Connection, test_user: User):
        """
        Test updating an existing user via save.
        """
        original_updated = test_user.updated_at
        test_user.email = "updated@example.com"

        await test_user.save()

        assert test_user.updated_at > original_updated

        # Verify in database
        email = await db_connection.fetchval(
            "SELECT email FROM users WHERE id = $1",
            test_user.id,
        )
        assert email == "updated@example.com"

    async def test_user_repr(self):
        """
        Test string representation of User.
        """
        user = User(email="test@example.com")
        assert str(user) == "<User id=None email=test@example.com>"

        user.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        assert "550e8400-e29b-41d4-a716-446655440000" in str(user)
        assert "test@example.com" in str(user)

    async def test_password_verification_flow(
        self, db_connection: Connection, clean_tables: None
    ):
        """
        Test complete password flow: hash, store, verify.
        """
        password = "MySecurePass123!"
        email = "security@example.com"

        # Create user with hashed password
        user = await User.create(
            email=email,
            password_hash=hash_password(password),
        )

        # Verify correct password
        assert verify_password(password, user.password_hash) is True

        # Verify incorrect password
        assert verify_password("WrongPass123!", user.password_hash) is False

        # Update password
        new_password = "EvenMoreSecure456!"
        await user.update_password(hash_password(new_password))

        # Old password should not work
        assert verify_password(password, user.password_hash) is False

        # New password should work
        assert verify_password(new_password, user.password_hash) is True
