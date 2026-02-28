import pytest
from database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before running tests"""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)
