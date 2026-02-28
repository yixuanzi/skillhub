import pytest
from models.user import User, Role, Permission, RefreshToken
from database import SessionLocal

@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    try:
        yield db
        db.rollback()  # Rollback after each test
    finally:
        db.close()

@pytest.fixture(autouse=True)
def cleanup_db(db):
    """Auto-use fixture to clean up database before each test"""
    # Clean up all data before each test
    db.query(RefreshToken).delete()
    db.query(User).delete()
    db.query(Permission).delete()
    db.query(Role).delete()
    db.commit()
    yield
    # Cleanup happens in db fixture's rollback

def test_create_user(db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True

def test_create_role_with_permissions(db):
    role = Role(name="admin", description="Administrator")
    perm1 = Permission(resource="skills", action="read")
    perm2 = Permission(resource="skills", action="write")

    role.permissions.extend([perm1, perm2])
    db.add(role)
    db.commit()
    db.refresh(role)

    assert len(role.permissions) == 2
    assert "read" in [p.action for p in role.permissions]
    assert "write" in [p.action for p in role.permissions]

def test_user_role_relationship(db):
    # Create role and permissions
    role = Role(name="editor", description="Content editor")
    perm = Permission(resource="skills", action="write")
    role.permissions.append(perm)
    db.add(role)
    db.commit()

    # Create user
    user = User(
        username="editoruser",
        email="editor@example.com",
        hashed_password="hashed_password"
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert len(user.roles) == 1
    assert user.roles[0].name == "editor"

def test_refresh_token(db):
    # Create user first
    user = User(
        username="tokenuser",
        email="token@example.com",
        hashed_password="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create refresh token
    from datetime import datetime, timedelta
    token = RefreshToken(
        token_hash="hashed_token_value",
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    assert token.id is not None
    assert token.user_id == user.id
    assert token.user.id == user.id
