"""Script to create the mtoken table."""
from database import engine, Base
from models.mtoken import MToken


def create_table():
    """Create the mtoken table."""
    print("Creating mtoken table...")
    Base.metadata.create_all(bind=engine, tables=[MToken.__table__])
    print("mtoken table created successfully!")


if __name__ == "__main__":
    create_table()
