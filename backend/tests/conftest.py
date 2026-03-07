import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal
# Import all models to ensure they're registered with Base
from models.user import User, RefreshToken, Role, Permission
from models.resource import Resource
from models.skill_list import SkillList
from models.api_key import APIKey
from models.mtoken import MToken
from models.system_audit_log import SystemAuditLog
from schemas.auth import UserCreate
from services.auth_service import AuthService
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before running tests"""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        # Clean up all data after each test using a fresh session
        cleanup_session = SessionLocal()
        try:
            cleanup_session.query(SystemAuditLog).delete()
            cleanup_session.query(SkillList).delete()
            cleanup_session.query(Resource).delete()
            cleanup_session.query(RefreshToken).delete()
            cleanup_session.query(User).delete()
            cleanup_session.query(Permission).delete()
            cleanup_session.query(Role).delete()
            cleanup_session.commit()
        except Exception:
            cleanup_session.rollback()
        finally:
            cleanup_session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    from database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: SessionLocal):
    """Create a test user fixture."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == "testuser").first()
    if existing_user:
        return existing_user

    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = AuthService.register(db, user_data)
    db.commit()
    return user


@pytest.fixture(scope="function")
def admin_user(db: SessionLocal):
    """Create admin user with role."""
    # Create admin role
    admin_role = Role(name="admin", description="Administrator")
    perm = Permission(resource="*", action="*")
    admin_role.permissions.append(perm)
    db.add(admin_role)
    db.commit()

    # Create admin user
    user_data = UserCreate(
        username="admin",
        email="admin@example.com",
        password="adminpassword123"
    )
    AuthService.register(db, user_data)
    # Query the actual User model
    user = db.query(User).filter(User.username == "admin").first()
    user.roles.append(admin_role)
    db.commit()
    db.refresh(user)
    return user
