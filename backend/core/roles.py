"""Built-in roles and the helpers that decide on them.

SkillHub deliberately has no permission matrix. Who may do what comes down to
three questions, asked in this order:

1. Is it yours? The owner of a resource, ACL rule, skill, API key or token
   manages it. This is the rule for everything a normal user does.
2. Are you an admin? `admin` and `super_admin` can additionally see and manage
   other people's resources, ACL rules and skills, read every audit log, and
   manage users and roles. `admin` is the limited one: it cannot grant
   `super_admin` or touch a `super_admin` account.
3. May you invoke it? That is the resource's ACL rule and nothing else - no
   role, not even `super_admin`, bypasses it (see ACLResourceService).

Roles carry no permissions of their own. `user` is simply the role every
account gets; custom roles created by an admin exist only so ACL rules can
grant access to a group of users at once.
"""
from typing import Optional, Set

from sqlalchemy.orm import Session

from models.user import Role, User

SUPER_ADMIN = "super_admin"
ADMIN = "admin"
USER = "user"

ADMIN_ROLES = frozenset({ADMIN, SUPER_ADMIN})

# name -> description, in the order they are seeded.
BUILTIN_ROLES = {
    SUPER_ADMIN: "Super administrator: everything an admin can do, plus managing super_admin accounts",
    ADMIN: "Administrator: manages users, roles and other people's resources",
    USER: "Regular user: manages what they own",
}


def role_names(user: Optional[User]) -> Set[str]:
    """Names of the roles `user` holds (empty for no user)."""
    if not user or not user.roles:
        return set()
    return {role.name for role in user.roles}


def is_admin_user(user: Optional[User]) -> bool:
    """True when the user holds `admin` or `super_admin`."""
    return bool(role_names(user) & ADMIN_ROLES)


def is_super_admin(user: Optional[User]) -> bool:
    """True when the user holds `super_admin`."""
    return SUPER_ADMIN in role_names(user)


def is_builtin_role(name: Optional[str]) -> bool:
    """True for a role name the code depends on, which must not be renamed or deleted."""
    return name in BUILTIN_ROLES


def get_or_create_role(db: Session, name: str) -> Role:
    """Return the built-in role `name`, creating it if the database was never seeded.

    Only flushes; the caller owns the transaction.
    """
    role = db.query(Role).filter(Role.name == name).first()
    if role is None:
        role = Role(name=name, description=BUILTIN_ROLES.get(name))
        db.add(role)
        db.flush()
    return role
