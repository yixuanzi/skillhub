import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal
from models.user import User, RefreshToken, Role, Permission
from schemas.auth import UserCreate
from services.auth_service import AuthService
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before running tests"""
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
    finally:
        session.close()
        # Clean up all data after each test
        session = SessionLocal()
        session.query(RefreshToken).delete()
        session.query(User).delete()
        session.query(Permission).delete()
        session.query(Role).delete()
        session.commit()
        session.close()


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
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = AuthService.register(db, user_data)
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
    user = AuthService.register(db, user_data)
    user.roles.append(admin_role)
    db.commit()
    db.refresh(user)
    return user
