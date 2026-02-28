"""Database initialization script.

Creates all database tables by importing models and calling init_db().
Run this script to set up a fresh database schema.
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db


def main():
    """Initialize database tables."""
    print("Initializing database...")

    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from models import (
            User, Role, Permission, RefreshToken,
            Skill, SkillVersion, SkillType, SkillRuntime, SkillStatus,
            ACLRule, ACLRuleRole, AuditLog, AccessMode, AuditResult
        )

        # Create all tables
        init_db()

        print("✓ Database initialized successfully!")
        print("  All tables have been created.")

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
