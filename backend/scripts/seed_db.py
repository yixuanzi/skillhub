"""Database seeding script.

Populates the database with default data:
- Permissions for all resources and actions
- Default roles (super_admin, admin, developer, operator, viewer)
- Default admin user (admin/admin123)
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.user import User, Role, Permission
from core.security import get_password_hash


def seed_permissions(db):
    """Create all permissions for resources and actions."""
    print("\nSeeding permissions...")

    # Define all resource+action combinations
    permissions_data = [
        # User permissions
        ("users", "read", "Read user information"),
        ("users", "write", "Create and update users"),
        ("users", "delete", "Delete users"),

        # Skill permissions
        ("skills", "read", "Read skill information"),
        ("skills", "write", "Create and update skills"),
        ("skills", "delete", "Delete skills"),
        ("skills", "build", "Build skills"),
        ("skills", "publish", "Publish skills"),
        ("skills", "invoke", "Invoke/call skills"),

        # ACL permissions
        ("acl", "read", "Read ACL rules and audit logs"),
        ("acl", "write", "Create and update ACL rules"),
        ("acl", "delete", "Delete ACL rules"),
    ]

    permissions = []
    for resource, action, description in permissions_data:
        # Check if permission already exists
        existing = db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action
        ).first()

        if existing:
            permissions.append(existing)
            print(f"  ✓ Permission already exists: {resource}:{action}")
        else:
            permission = Permission(
                resource=resource,
                action=action,
                description=description
            )
            db.add(permission)
            permissions.append(permission)
            print(f"  + Created permission: {resource}:{action}")

    db.flush()  # Flush to get IDs
    return permissions


def seed_roles(db, permissions):
    """Create default roles with assigned permissions."""
    print("\nSeeding roles...")

    # Create a lookup dictionary for permissions
    perm_dict = {}
    for perm in permissions:
        key = f"{perm.resource}:{perm.action}"
        perm_dict[key] = perm

    # Define role configurations
    roles_data = [
        {
            "name": "super_admin",
            "description": "Super administrator with full system access",
            "permissions": list(perm_dict.values())  # All permissions
        },
        {
            "name": "admin",
            "description": "Administrator with read/write access",
            "permissions": [
                perm_dict["users:read"],
                perm_dict["users:write"],
                perm_dict["skills:read"],
                perm_dict["skills:write"],
                perm_dict["acl:read"],
                perm_dict["acl:write"],
            ]
        },
        {
            "name": "developer",
            "description": "Developer with skill development access",
            "permissions": [
                perm_dict["skills:read"],
                perm_dict["skills:write"],
                perm_dict["skills:build"],
                perm_dict["skills:publish"],
            ]
        },
        {
            "name": "operator",
            "description": "Operator with skill execution access",
            "permissions": [
                perm_dict["skills:read"],
                perm_dict["skills:invoke"],
                perm_dict["acl:read"],
            ]
        },
        {
            "name": "viewer",
            "description": "Viewer with read-only access",
            "permissions": [
                perm_dict["users:read"],
                perm_dict["skills:read"],
                perm_dict["acl:read"],
            ]
        },
    ]

    roles = []
    for role_data in roles_data:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()

        if existing:
            roles.append(existing)
            print(f"  ✓ Role already exists: {role_data['name']}")
        else:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )
            role.permissions = role_data["permissions"]
            db.add(role)
            roles.append(role)
            print(f"  + Created role: {role_data['name']}")

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
    super_admin_role = next((r for r in roles if r.name == "super_admin"), None)
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

    db = SessionLocal()

    try:
        # Create permissions first
        permissions = seed_permissions(db)

        # Create roles with permissions
        roles = seed_roles(db, permissions)

        # Create admin user
        seed_admin_user(db, roles)

        # Commit all changes
        db.commit()

        print("\n" + "=" * 50)
        print("✓ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - Permissions: {len(permissions)}")
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
