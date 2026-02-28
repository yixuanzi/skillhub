"""Unit tests for MTokenService.

Tests the business logic layer for token management operations.
"""
import pytest
from sqlalchemy.orm import Session
from models.mtoken import MToken
from schemas.mtoken import MTokenCreate, MTokenUpdate
from services.mtoken_service import MTokenService
from core.exceptions import NotFoundException


class TestMTokenServiceCreate:
    """Tests for token creation."""

    def test_create_token_success(self, db: Session):
        """Test successful token creation."""
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Personal Access Token",
            value="ghp_xxxxxxxxxxxxxxxxxxxx",
            desc="My GitHub token"
        )

        result = MTokenService.create(db, data, "test-user-id")

        assert result.id is not None
        assert result.app_name == "GitHub"
        assert result.key_name == "Personal Access Token"
        assert result.value == "ghp_xxxxxxxxxxxxxxxxxxxx"
        assert result.created_by == "test-user-id"

    def test_create_multiple_tokens(self, db: Session):
        """Test creating multiple tokens for same user."""
        # Create first token
        data1 = MTokenCreate(
            app_name="OpenAI",
            key_name="API Key",
            value="sk-xxxxxxxxxxxx"
        )
        MTokenService.create(db, data1, "user-1")

        # Create second token for same user
        data2 = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="ghp_xxxxx"
        )
        MTokenService.create(db, data2, "user-1")

        # Create token for different user
        data3 = MTokenCreate(
            app_name="OpenAI",
            key_name="API Key",
            value="sk-yyyyyyyy"
        )
        MTokenService.create(db, data3, "user-2")

        # User 1 should have 2 tokens
        count = MTokenService.count_all(db, "user-1")
        assert count == 2

        # User 2 should have 1 token
        count = MTokenService.count_all(db, "user-2")
        assert count == 1


class TestMTokenServiceGet:
    """Tests for token retrieval."""

    def test_get_by_id_found(self, db: Session):
        """Test getting a token by ID when it exists and belongs to user."""
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="ghp_xxx",
            desc="Test"
        )
        created = MTokenService.create(db, data, "user-1")

        result = MTokenService.get_by_id(db, created.id, "user-1")

        assert result is not None
        assert result.id == created.id
        assert result.app_name == "GitHub"

    def test_get_by_id_not_found(self, db: Session):
        """Test getting a token by ID when it doesn't exist."""
        result = MTokenService.get_by_id(db, "non-existent-id", "user-1")
        assert result is None

    def test_get_by_id_wrong_user(self, db: Session):
        """Test getting a token created by another user."""
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="ghp_xxx"
        )
        created = MTokenService.create(db, data, "user-1")

        # User 2 tries to access user 1's token
        result = MTokenService.get_by_id(db, created.id, "user-2")
        assert result is None  # Should not be able to access


class TestMTokenServiceList:
    """Tests for token listing and filtering."""

    def test_list_all_with_pagination(self, db: Session):
        """Test listing all tokens with pagination."""
        user_id = "test-user"

        # Create multiple tokens
        for i in range(5):
            data = MTokenCreate(
                app_name=f"App{i}",
                key_name=f"Key{i}",
                value=f"value{i}"
            )
            MTokenService.create(db, data, user_id)

        mtokens = MTokenService.list_all(db, user_id, skip=0, limit=3)

        assert len(mtokens) == 3

    def test_list_by_app(self, db: Session):
        """Test filtering tokens by app name."""
        user_id = "test-user"

        # Create tokens with different app names
        data1 = MTokenCreate(
            app_name="GitHub",
            key_name="Token1",
            value="value1"
        )
        data2 = MTokenCreate(
            app_name="OpenAI",
            key_name="Token2",
            value="value2"
        )
        MTokenService.create(db, data1, user_id)
        MTokenService.create(db, data2, user_id)

        mtokens = MTokenService.list_by_app(db, user_id, "GitHub")

        assert len(mtokens) == 1
        assert mtokens[0].app_name == "GitHub"

    def test_list_user_isolation(self, db: Session):
        """Test that users only see their own tokens."""
        # Create tokens for user 1
        for i in range(3):
            data = MTokenCreate(
                app_name=f"App{i}",
                key_name=f"Key{i}",
                value=f"user1_value{i}"
            )
            MTokenService.create(db, data, "user-1")

        # Create tokens for user 2
        for i in range(2):
            data = MTokenCreate(
                app_name=f"App{i}",
                key_name=f"Key{i}",
                value=f"user2_value{i}"
            )
            MTokenService.create(db, data, "user-2")

        # User 1 should only see 3 tokens
        user1_tokens = MTokenService.list_all(db, "user-1")
        assert len(user1_tokens) == 3

        # User 2 should only see 2 tokens
        user2_tokens = MTokenService.list_all(db, "user-2")
        assert len(user2_tokens) == 2

    def test_count_all(self, db: Session):
        """Test counting all tokens for a user."""
        user_id = "test-user"
        initial_count = MTokenService.count_all(db, user_id)

        # Create 3 tokens
        for i in range(3):
            data = MTokenCreate(
                app_name=f"App{i}",
                key_name=f"Key{i}",
                value=f"value{i}"
            )
            MTokenService.create(db, data, user_id)

        final_count = MTokenService.count_all(db, user_id)
        assert final_count == initial_count + 3


class TestMTokenServiceUpdate:
    """Tests for token updates."""

    def test_update_token_success(self, db: Session):
        """Test successful token update."""
        user_id = "test-user"
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Old Name",
            value="old_value"
        )
        created = MTokenService.create(db, data, user_id)

        update_data = MTokenUpdate(
            app_name="GitHub",
            key_name="New Name",
            value="new_value"
        )
        result = MTokenService.update(db, created.id, user_id, update_data)

        assert result.key_name == "New Name"
        assert result.value == "new_value"

    def test_update_token_wrong_user(self, db: Session):
        """Test updating token created by another user."""
        # Create token for user 1
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="value1"
        )
        created = MTokenService.create(db, data, "user-1")

        # User 2 tries to update user 1's token
        update_data = MTokenUpdate(
            value="hacked_value"
        )

        with pytest.raises(NotFoundException) as exc_info:
            MTokenService.update(db, created.id, "user-2", update_data)

        assert "not found" in str(exc_info.value)

    def test_update_token_not_found(self, db: Session):
        """Test that updating non-existent token raises NotFoundException."""
        update_data = MTokenUpdate(value="new_value")

        with pytest.raises(NotFoundException) as exc_info:
            MTokenService.update(db, "non-existent-id", "user-1", update_data)

        assert "not found" in str(exc_info.value)


class TestMTokenServiceDelete:
    """Tests for token deletion."""

    def test_delete_token_success(self, db: Session):
        """Test successful token deletion."""
        user_id = "test-user"
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="value"
        )
        created = MTokenService.create(db, data, user_id)

        result = MTokenService.delete(db, created.id, user_id)

        assert result is True

        # Verify deletion
        mtoken = MTokenService.get_by_id(db, created.id, user_id)
        assert mtoken is None

    def test_delete_token_wrong_user(self, db: Session):
        """Test deleting token created by another user."""
        # Create token for user 1
        data = MTokenCreate(
            app_name="GitHub",
            key_name="Token",
            value="value1"
        )
        created = MTokenService.create(db, data, "user-1")

        # User 2 tries to delete user 1's token
        with pytest.raises(NotFoundException) as exc_info:
            MTokenService.delete(db, created.id, "user-2")

        assert "not found" in str(exc_info.value)

    def test_delete_token_not_found(self, db: Session):
        """Test that deleting non-existent token raises NotFoundException."""
        with pytest.raises(NotFoundException) as exc_info:
            MTokenService.delete(db, "non-existent-id", "user-1")

        assert "not found" in str(exc_info.value)
