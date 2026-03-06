"""Script to create the api_keys table."""
from database import engine, Base
from models.api_key import APIKey


def create_table():
    """Create the api_keys table."""
    print("Creating api_keys table...")
    Base.metadata.create_all(bind=engine, tables=[APIKey.__table__])
    print("api_keys table created successfully!")


if __name__ == "__main__":
    create_table()
