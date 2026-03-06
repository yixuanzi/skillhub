"""Script to migrate resources table to v1.1b - Add view_scope, owner_id, api_description, and MCP fields."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, Base
from models.resource import Resource


def migrate():
    """Migrate resources table to v1.1b."""
    print("Migrating resources table to v1.1b...")

    with engine.connect() as conn:
        # Check if columns already exist
        inspector_result = conn.execute(text("PRAGMA table_info(resources)"))
        existing_columns = {row[1] for row in inspector_result}

        # Add view_scope column if not exists
        if 'view_scope' not in existing_columns:
            print("Adding view_scope column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN view_scope VARCHAR(20) DEFAULT 'public' NOT NULL"
            ))
            conn.commit()
        else:
            print("view_scope column already exists")

        # Add owner_id column if not exists
        if 'owner_id' not in existing_columns:
            print("Adding owner_id column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN owner_id VARCHAR(36)"
            ))
            conn.commit()
        else:
            print("owner_id column already exists")

        # Add api_description column if not exists
        if 'api_description' not in existing_columns:
            print("Adding api_description column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN api_description TEXT"
            ))
            conn.commit()
        else:
            print("api_description column already exists")

        # Add mcp_server_type column if not exists
        if 'mcp_server_type' not in existing_columns:
            print("Adding mcp_server_type column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN mcp_server_type VARCHAR(50)"
            ))
            conn.commit()
        else:
            print("mcp_server_type column already exists")

        # Add mcp_command column if not exists
        if 'mcp_command' not in existing_columns:
            print("Adding mcp_command column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN mcp_command VARCHAR(500)"
            ))
            conn.commit()
        else:
            print("mcp_command column already exists")

        # Add mcp_args column if not exists
        if 'mcp_args' not in existing_columns:
            print("Adding mcp_args column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN mcp_args TEXT"
            ))
            conn.commit()
        else:
            print("mcp_args column already exists")

        # Add mcp_env column if not exists
        if 'mcp_env' not in existing_columns:
            print("Adding mcp_env column...")
            conn.execute(text(
                "ALTER TABLE resources ADD COLUMN mcp_env TEXT"
            ))
            conn.commit()
        else:
            print("mcp_env column already exists")

        # Create indexes
        print("Creating indexes...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_resources_view_scope ON resources (view_scope)"))
            conn.commit()
            print("ix_resources_view_scope index created/exists")
        except Exception as e:
            print(f"Note: {e}")

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_resources_owner_id ON resources (owner_id)"))
            conn.commit()
            print("ix_resources_owner_id index created/exists")
        except Exception as e:
            print(f"Note: {e}")

    print("Resources table migration to v1.1b completed successfully!")


def rollback():
    """Rollback resources table migration v1.1b."""
    print("Rolling back resources table migration v1.1b...")
    print("WARNING: SQLite does not support DROP COLUMN. This is a no-op.")
    print("To rollback, you would need to recreate the table without the new columns.")
    print("This would require exporting data, dropping table, recreating, and re-importing.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate resources table to v1.1b")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
