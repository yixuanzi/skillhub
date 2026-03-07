"""Script to migrate resources table to v1.2 - Add view_scope and api_description fields.

This migration adds:
1. view_scope field for controlling resource visibility
2. api_description field for API documentation (markdown)
MCP configuration will be stored in the existing ext field as JSON.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def migrate():
    """Migrate resources table to v1.2 - Add view_scope and api_description."""
    print("Migrating resources table to v1.2...")

    with engine.connect() as conn:
        # Check if columns already exist
        inspector_result = conn.execute(text("PRAGMA table_info(resources)"))
        existing_columns = {row[1] for row in inspector_result}

        # Add view_scope column if not exists
        if 'view_scope' not in existing_columns:
            print("Adding view_scope column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN view_scope VARCHAR(50) DEFAULT 'private' NOT NULL"
            ))
            conn.commit()
            print("view_scope column added with default 'private'")
        else:
            print("view_scope column already exists")

        # Add api_description column if not exists
        if 'api_description' not in existing_columns:
            print("Adding api_description column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN api_description TEXT"
            ))
            conn.commit()
            print("api_description column added")
        else:
            print("api_description column already exists")

        # Create index for view_scope
        print("Creating indexes...")
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_resource_view_scope ON resources (view_scope)"
            ))
            conn.commit()
            print("ix_resource_view_scope index created/exists")
        except Exception as e:
            print(f"Note creating index: {e}")

    print("Resources table migration to v1.2 completed successfully!")


def rollback():
    """Rollback resources table migration v1.2.

    Note: SQLite does not support DROP COLUMN. To rollback, you would need to:
    1. Export data
    2. Drop table
    3. Recreate table without view_scope
    4. Re-import data
    """
    print("Rolling back resources table migration v1.2...")
    print("WARNING: SQLite does not support DROP COLUMN.")
    print("To rollback, you would need to recreate the table without the new columns.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate resources table to v1.2")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
