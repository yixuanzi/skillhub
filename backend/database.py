from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables"""
    # Import every model before create_all so the legacy startup path also
    # registers the OIDC tables. This import is intentionally local to avoid a
    # database -> models import cycle during module initialization.
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # SQLAlchemy create_all does not alter existing SQLite tables. Keep the
    # existing demo database usable when OIDC support is added later.
    if engine.dialect.name == "sqlite":
        inspector = inspect(engine)
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as connection:
            if "oidc_subject" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN oidc_subject VARCHAR"))
            connection.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_oidc_subject "
                "ON users (oidc_subject) WHERE oidc_subject IS NOT NULL"
            ))
