"""Database seeding script.

Populates the database with default data:
- The built-in roles (super_admin, admin, user) - see core/roles.py
- Default admin user (admin/admin123), holding super_admin

Roles carry no permissions, so there is nothing else to seed. To bring an
existing database in line with the built-in roles, run
scripts/migrate_roles.py instead.
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models.user import User, Role
from core.roles import BUILTIN_ROLES, SUPER_ADMIN
from core.security import get_password_hash


def seed_roles(db):
    """Create the built-in roles."""
    print("\nSeeding roles...")

    roles = []
    for name, description in BUILTIN_ROLES.items():
        existing = db.query(Role).filter(Role.name == name).first()

        if existing:
            roles.append(existing)
            print(f"  ✓ Role already exists: {name}")
        else:
            role = Role(name=name, description=description)
            db.add(role)
            roles.append(role)
            print(f"  + Created role: {name}")

    db.flush()  # Flush to get IDs
    return roles


def seed_admin_user(db, roles):
    """Create default admin user."""
    print("\nSeeding admin user...")

    # Check if admin user already exists
    existing = db.query(User).filter(User.username == "admin").first()

    if existing:
        print(f"  ✓ Admin user already exists: admin")
        return

    # Get super_admin role
    super_admin_role = next((r for r in roles if r.name == SUPER_ADMIN), None)
    if not super_admin_role:
        raise ValueError("super_admin role not found!")

    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@skillhub.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True
    )
    admin_user.roles = [super_admin_role]

    db.add(admin_user)
    print(f"  + Created admin user: admin / admin123")
    print(f"    Email: admin@skillhub.com")
    print(f"    Role: super_admin")


def main():
    """Seed database with default data."""
    print("Seeding database with default data...")
    print("=" * 50)

    # Initialize database tables first
    print("\nInitializing database tables...")
    init_db()
    print("  ✓ Database tables initialized")

    db = SessionLocal()

    try:
        roles = seed_roles(db)

        # Create admin user
        seed_admin_user(db, roles)

        # Commit all changes
        db.commit()

        print("\n" + "=" * 50)
        print("✓ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - Roles: {len(roles)}")
        print(f"  - Admin user: admin / admin123")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
