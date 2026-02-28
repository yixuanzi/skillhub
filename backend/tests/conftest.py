import pytest
from database import Base, engine, SessionLocal
from models.user import User, RefreshToken


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
        session.commit()
        session.close()
