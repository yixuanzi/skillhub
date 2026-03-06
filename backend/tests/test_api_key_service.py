"""Unit tests for API Key Service.

This test suite covers:
- API key generation and hashing
- API key creation with validation
- API key listing and retrieval
- API key update
- API key revocation
- API key rotation
- API key authentication
- Scope validation
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from models.api_key import APIKey
from models.user import User
from schemas.api_key import APIKeyCreate, APIKeyUpdate, APIScope
from services.api_key_service import APIKeyService
from core.exceptions import ValidationException, NotFoundException


class TestAPIKeyGeneration:
    """Test suite for API key generation."""

    def test_generate_api_key_format(self):
        """Test that generated API key has correct format."""
        full_key, key_hash, key_prefix = APIKeyService.generate_api_key()

        # Full key should start with "sk_" and be longer than prefix
        assert full_key.startswith("sk_")
        assert len(full_key) > len(key_prefix)
        assert len(key_prefix) == 10
        assert key_prefix == full_key[:10]

        # Hash should be 64 characters (SHA256 hex)
        assert len(key_hash) == 64

    def test_generate_unique_keys(self):
        """Test that each generated key is unique."""
        keys = set()
        for _ in range(100):
            full_key, _, _ = APIKeyService.generate_api_key()
            keys.add(full_key)

        # All 100 keys should be unique
        assert len(keys) == 100

    def test_key_hashing_consistent(self):
        """Test that hashing the same key produces the same hash."""
        full_key, key_hash1, _ = APIKeyService.generate_api_key()
        import hashlib
        key_hash2 = hashlib.sha256(full_key.encode()).hexdigest()

        assert key_hash1 == key_hash2


class TestAPIKeyCreate:
    """Test suite for API key creation."""

    def test_create_api_key_success(self, db: Session, test_user: User):
        """Test successful API key creation."""
        data = APIKeyCreate(
            name="Test Key",
            scopes=[APIScope.SKILLS_READ, APIScope.RESOURCES_READ]
        )

        api_key, full_key = APIKeyService.create(db, test_user, data)

        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.user_id == test_user.id
        assert api_key.is_active is True
        assert len(api_key.scopes) == 2
        assert api_key.key_prefix == full_key[:10]
        assert full_key.startswith("sk_")

    def test_create_api_key_with_expiration(self, db: Session, test_user: User):
        """Test API key creation with expiration date."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        data = APIKeyCreate(
            name="Expiring Key",
            scopes=[APIScope.SKILLS_READ],
            expires_at=expires_at
        )

        api_key, _ = APIKeyService.create(db, test_user, data)

        assert api_key.expires_at is not None
        # Compare as naive datetimes (SQLite doesn't preserve timezone)
        expires_at_naive = expires_at.replace(tzinfo=None)
        api_key_expires_naive = api_key.expires_at.replace(tzinfo=None) if api_key.expires_at.tzinfo else api_key.expires_at
        assert abs((api_key_expires_naive - expires_at_naive).total_seconds()) < 5

    def test_create_api_key_invalid_scope(self, db: Session, test_user: User):
        """Test API key creation with invalid scope fails."""
        data = APIKeyCreate(
            name="Invalid Scope Key",
            scopes=["invalid:scope"]
        )

        with pytest.raises(ValidationException) as exc:
            APIKeyService.create(db, test_user, data)

        assert "Invalid scopes" in str(exc.value)

    def test_create_api_key_max_keys_limit(self, db: Session, test_user: User):
        """Test that max active keys limit is enforced."""
        # Create MAX_ACTIVE_KEYS keys
        for i in range(APIKeyService.MAX_ACTIVE_KEYS):
            data = APIKeyCreate(
                name=f"Key {i}",
                scopes=[APIScope.SKILLS_READ]
            )
            APIKeyService.create(db, test_user, data)

        # Try to create one more
        data = APIKeyCreate(
            name="Extra Key",
            scopes=[APIScope.SKILLS_READ]
        )

        with pytest.raises(ValidationException) as exc:
            APIKeyService.create(db, test_user, data)

        assert "Maximum" in str(exc.value)
        assert "active API keys allowed" in str(exc.value)


class TestAPIKeyList:
    """Test suite for API key listing."""

    def test_list_by_user_empty(self, db: Session, test_user: User):
        """Test listing API keys when user has none."""
        keys = APIKeyService.list_by_user(db, str(test_user.id))
        assert len(keys) == 0

    def test_list_by_user_with_keys(self, db: Session, test_user: User):
        """Test listing API keys returns user's keys only."""
        # Create keys for test user
        for i in range(3):
            data = APIKeyCreate(name=f"Key {i}", scopes=[APIScope.SKILLS_READ])
            APIKeyService.create(db, test_user, data)

        keys = APIKeyService.list_by_user(db, str(test_user.id))
        assert len(keys) == 3

    def test_list_by_user_pagination(self, db: Session, test_user: User):
        """Test pagination of API key listing."""
        # Create 5 keys
        for i in range(5):
            data = APIKeyCreate(name=f"Key {i}", scopes=[APIScope.SKILLS_READ])
            APIKeyService.create(db, test_user, data)

        # Get first page
        keys = APIKeyService.list_by_user(db, str(test_user.id), skip=0, limit=3)
        assert len(keys) == 3

        # Get second page
        keys = APIKeyService.list_by_user(db, str(test_user.id), skip=3, limit=3)
        assert len(keys) == 2

    def test_list_by_user_returns_newest_first(self, db: Session, test_user: User):
        """Test that keys are ordered by creation date descending."""
        # Create keys with delays
        key1, _ = APIKeyService.create(db, test_user, APIKeyCreate(name="Key 1", scopes=[APIScope.SKILLS_READ]))
        key2, _ = APIKeyService.create(db, test_user, APIKeyCreate(name="Key 2", scopes=[APIScope.SKILLS_READ]))

        keys = APIKeyService.list_by_user(db, str(test_user.id))
        assert keys[0].id == key2.id  # Newest first
        assert keys[1].id == key1.id


class TestAPIKeyGet:
    """Test suite for API key retrieval."""

    def test_get_by_id_found(self, db: Session, test_user: User):
        """Test getting API key by ID."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        retrieved_key = APIKeyService.get_by_id(db, created_key.id, str(test_user.id))

        assert retrieved_key.id == created_key.id
        assert retrieved_key.name == "Test Key"

    def test_get_by_id_not_found(self, db: Session, test_user: User):
        """Test getting non-existent API key raises error."""
        with pytest.raises(NotFoundException) as exc:
            APIKeyService.get_by_id(db, "non-existent-id", str(test_user.id))

        assert "not found" in str(exc.value)

    def test_get_by_id_wrong_user(self, db: Session, test_user: User, admin_user: User):
        """Test getting another user's API key raises error."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        with pytest.raises(NotFoundException):
            APIKeyService.get_by_id(db, created_key.id, str(admin_user.id))


class TestAPIKeyUpdate:
    """Test suite for API key update."""

    def test_update_name(self, db: Session, test_user: User):
        """Test updating API key name."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Old Name", scopes=[APIScope.SKILLS_READ])
        )

        updated_key = APIKeyService.update(
            db, created_key.id, str(test_user.id),
            APIKeyUpdate(name="New Name")
        )

        assert updated_key.name == "New Name"
        assert updated_key.scopes == created_key.scopes  # Scopes unchanged

    def test_update_scopes(self, db: Session, test_user: User):
        """Test updating API key scopes."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        updated_key = APIKeyService.update(
            db, created_key.id, str(test_user.id),
            APIKeyUpdate(scopes=[APIScope.SKILLS_READ, APIScope.SKILLS_CALL])
        )

        assert len(updated_key.scopes) == 2
        assert APIScope.SKILLS_CALL in updated_key.scopes

    def test_update_expiration(self, db: Session, test_user: User):
        """Test updating API key expiration."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        new_expires_at = datetime.now(timezone.utc) + timedelta(days=60)
        updated_key = APIKeyService.update(
            db, created_key.id, str(test_user.id),
            APIKeyUpdate(expires_at=new_expires_at)
        )

        assert updated_key.expires_at is not None
        # Compare as naive datetimes
        new_expires_naive = new_expires_at.replace(tzinfo=None)
        updated_expires_naive = updated_key.expires_at.replace(tzinfo=None) if updated_key.expires_at.tzinfo else updated_key.expires_at
        assert abs((updated_expires_naive - new_expires_naive).total_seconds()) < 5

    def test_update_deactivate(self, db: Session, test_user: User):
        """Test deactivating API key via update."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        updated_key = APIKeyService.update(
            db, created_key.id, str(test_user.id),
            APIKeyUpdate(is_active=False)
        )

        assert updated_key.is_active is False

    def test_update_invalid_scopes(self, db: Session, test_user: User):
        """Test update with invalid scopes raises error."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        with pytest.raises(ValidationException) as exc:
            APIKeyService.update(
                db, created_key.id, str(test_user.id),
                APIKeyUpdate(scopes=["invalid:scope"])
            )

        assert "Invalid scopes" in str(exc.value)


class TestAPIKeyRevoke:
    """Test suite for API key revocation."""

    def test_revoke_api_key(self, db: Session, test_user: User):
        """Test revoking an API key."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        revoked_key = APIKeyService.revoke(db, created_key.id, str(test_user.id))

        assert revoked_key.is_active is False
        assert revoked_key.id == created_key.id

    def test_revoke_already_revoked_key(self, db: Session, test_user: User):
        """Test revoking an already revoked key."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        # Revoke once
        APIKeyService.revoke(db, created_key.id, str(test_user.id))

        # Revoke again - should work but key remains inactive
        revoked_key = APIKeyService.revoke(db, created_key.id, str(test_user.id))
        assert revoked_key.is_active is False


class TestAPIKeyRotate:
    """Test suite for API key rotation."""

    def test_rotate_api_key(self, db: Session, test_user: User):
        """Test rotating an API key generates new key."""
        created_key, old_key = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        # Store original prefix before rotation
        original_prefix = created_key.key_prefix
        original_name = created_key.name
        original_scopes = created_key.scopes

        rotated_key, new_key = APIKeyService.rotate(db, created_key.id, str(test_user.id))

        # New key should be different
        assert new_key != old_key

        # Prefix should be different from the original
        assert rotated_key.key_prefix != original_prefix

        # Name, scopes, expiration should be preserved
        assert rotated_key.name == original_name
        assert rotated_key.scopes == original_scopes
        assert rotated_key.is_active is True
        assert rotated_key.id == created_key.id  # Same record

    def test_rotate_preserves_expiration(self, db: Session, test_user: User):
        """Test that rotation preserves expiration date."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ], expires_at=expires_at)
        )

        rotated_key, _ = APIKeyService.rotate(db, created_key.id, str(test_user.id))

        assert rotated_key.expires_at is not None
        # Compare as naive datetimes
        expires_naive = expires_at.replace(tzinfo=None)
        rotated_naive = rotated_key.expires_at.replace(tzinfo=None) if rotated_key.expires_at.tzinfo else rotated_key.expires_at
        assert abs((rotated_naive - expires_naive).total_seconds()) < 5


class TestAPIKeyAuthentication:
    """Test suite for API key authentication."""

    def test_authenticate_valid_key(self, db: Session, test_user: User):
        """Test authenticating with valid API key."""
        _, full_key = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        authenticated_key = APIKeyService.authenticate(db, full_key)

        assert authenticated_key is not None
        assert authenticated_key.is_active is True
        assert authenticated_key.user_id == test_user.id

    def test_authenticate_updates_last_used(self, db: Session, test_user: User):
        """Test that authentication updates last_used_at timestamp."""
        created_key, full_key = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        assert created_key.last_used_at is None

        APIKeyService.authenticate(db, full_key)

        # Refresh from DB
        db.refresh(created_key)
        assert created_key.last_used_at is not None

    def test_authenticate_invalid_key(self, db: Session):
        """Test authenticating with invalid key returns None."""
        result = APIKeyService.authenticate(db, "invalid_key_xyz")
        assert result is None

    def test_authenticate_inactive_key(self, db: Session, test_user: User):
        """Test authenticating with inactive key returns None."""
        created_key, full_key = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        # Revoke the key
        APIKeyService.revoke(db, created_key.id, str(test_user.id))

        result = APIKeyService.authenticate(db, full_key)
        assert result is None

    def test_authenticate_expired_key(self, db: Session, test_user: User):
        """Test authenticating with expired key returns None."""
        # Create key with past expiration
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        created_key, full_key = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ], expires_at=expires_at)
        )

        # Force refresh to see the actual stored value
        db.refresh(created_key)

        result = APIKeyService.authenticate(db, full_key)
        assert result is None


class TestAPIKeyScopes:
    """Test suite for API key scope checking."""

    def test_has_scope_true(self, db: Session, test_user: User):
        """Test checking existing scope returns True."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ, APIScope.SKILLS_CALL])
        )

        assert APIKeyService.has_scope(created_key, APIScope.SKILLS_READ) is True
        assert APIKeyService.has_scope(created_key, APIScope.SKILLS_CALL) is True

    def test_has_scope_false(self, db: Session, test_user: User):
        """Test checking non-existing scope returns False."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        assert APIKeyService.has_scope(created_key, APIScope.SKILLS_CALL) is False
        assert APIKeyService.has_scope(created_key, APIScope.RESOURCES_WRITE) is False


class TestAPIScope:
    """Test suite for APIScope utility class."""

    def test_all_scopes_returns_valid_list(self):
        """Test that all_scopes returns non-empty list."""
        scopes = APIScope.all_scopes()
        assert len(scopes) > 0
        assert APIScope.SKILLS_READ in scopes
        assert APIScope.RESOURCES_READ in scopes

    def test_validate_scopes_with_valid_scopes(self):
        """Test validating valid scopes returns them."""
        scopes = [APIScope.SKILLS_READ, APIScope.RESOURCES_READ]
        result = APIScope.validate_scopes(scopes)
        assert result == scopes

    def test_validate_scopes_with_invalid_scopes(self):
        """Test validating invalid scopes raises ValueError."""
        with pytest.raises(ValueError) as exc:
            APIScope.validate_scopes(["invalid:scope"])

        assert "Invalid scopes" in str(exc.value)

    def test_validate_scopes_with_mixed_scopes(self):
        """Test validating mixed valid/invalid scopes raises error."""
        with pytest.raises(ValueError):
            APIScope.validate_scopes([APIScope.SKILLS_READ, "invalid:scope"])
