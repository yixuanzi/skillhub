#!/usr/bin/env python3
"""Bring an existing database in line with the built-in roles.

SkillHub used to seed five roles (super_admin, admin, developer, operator,
viewer) and a permissions table that nothing ever consulted. The role model is
now three built-in roles - super_admin, admin, user - with no permissions (see
core/roles.py). A freshly seeded database is already in that shape; this script
converts an older one:

- `viewer` is renamed to `user`. The role keeps its id, so ACL role bindings
  that point at it keep working. If `user` already exists, viewer's members
  and bindings are merged into it instead.
- `developer` and `operator` are deleted. Their members get `user`. ACL grants
  made to those two roles (role bindings, and entries in a rule's
  conditions.roles whitelist) are REMOVED rather than moved to `user`: moving
  them would open the resource to every account. Each removal is printed, so
  re-grant by user or by a custom role where it was intended.
- A `viewer` entry in a conditions.roles whitelist becomes `user`.
- Accounts with no role at all get `user`.
- Missing built-in roles are created.
- The unused `role_permissions` and `permissions` tables are dropped.

Custom roles, super_admin and admin memberships, and ACL rules that do not
mention the three legacy roles are not touched. Safe to run more than once.

Usage:
    python scripts/migrate_roles.py            # dry run, prints the plan
    python scripts/migrate_roles.py --apply    # write the changes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text  # noqa: E402

from core.roles import BUILTIN_ROLES, USER  # noqa: E402
from database import SessionLocal  # noqa: E402
from models.acl import ACLRule, ACLRuleRole  # noqa: E402
from models.user import Role, User  # noqa: E402

RENAMED_ROLE = "viewer"
REMOVED_ROLES = ("developer", "operator")
OBSOLETE_TABLES = ("role_permissions", "permissions")  # child table first


def _rule_label(db, acl_rule_id):
    rule = db.query(ACLRule).filter(ACLRule.id == acl_rule_id).first()
    return f"'{rule.resource_name}'" if rule else f"<missing rule {acl_rule_id}>"


def _merge_into(db, source, target, log):
    """Move `source`'s members and ACL bindings onto `target`."""
    for member in list(source.users):
        if target not in member.roles:
            member.roles.append(target)
        member.roles.remove(source)
        log.append(f"user '{member.username}': {source.name} -> {target.name}")

    target_rules = {
        binding.acl_rule_id
        for binding in db.query(ACLRuleRole).filter(ACLRuleRole.role_id == target.id)
    }
    for binding in db.query(ACLRuleRole).filter(ACLRuleRole.role_id == source.id).all():
        if binding.acl_rule_id in target_rules:
            db.delete(binding)
        else:
            binding.role_id = target.id
        log.append(f"ACL binding on {_rule_label(db, binding.acl_rule_id)}: {source.name} -> {target.name}")


def migrate(db):
    """Apply the role migration to `db`'s open transaction; return what changed.

    Does not commit - the caller commits to apply, or rolls back for a dry
    run. Dropping the obsolete tables is separate (see drop_obsolete_tables)
    because DDL does not roll back cleanly on every backend.
    """
    log = []

    # 1. viewer -> user
    viewer = db.query(Role).filter(Role.name == RENAMED_ROLE).first()
    user_role = db.query(Role).filter(Role.name == USER).first()
    # entries in conditions.roles to rewrite: old value -> new value (None = drop)
    rewrites = {}
    if viewer is not None:
        if user_role is None:
            viewer.name = USER
            viewer.description = BUILTIN_ROLES[USER]
            user_role = viewer
            log.append(f"role '{RENAMED_ROLE}' renamed to '{USER}'")
        else:
            _merge_into(db, viewer, user_role, log)
            rewrites[str(viewer.id)] = str(user_role.id)
            db.delete(viewer)
            log.append(f"role '{RENAMED_ROLE}' merged into existing '{USER}' and deleted")
        rewrites[RENAMED_ROLE] = USER
    # SessionLocal does not autoflush, so the queries below would not see the
    # rename without this.
    db.flush()

    # 2. make sure every built-in role exists
    for name, description in BUILTIN_ROLES.items():
        if db.query(Role).filter(Role.name == name).first() is None:
            db.add(Role(name=name, description=description))
            log.append(f"role '{name}' created")
    db.flush()
    user_role = db.query(Role).filter(Role.name == USER).first()

    # 3. developer / operator
    for name in REMOVED_ROLES:
        role = db.query(Role).filter(Role.name == name).first()
        rewrites[name] = None
        if role is None:
            continue
        rewrites[str(role.id)] = None
        for member in list(role.users):
            if user_role not in member.roles:
                member.roles.append(user_role)
            member.roles.remove(role)
            log.append(f"user '{member.username}': {name} -> {USER}")
        for binding in db.query(ACLRuleRole).filter(ACLRuleRole.role_id == role.id).all():
            log.append(f"ACCESS REMOVED: role binding for '{name}' on {_rule_label(db, binding.acl_rule_id)}")
            db.delete(binding)
        db.delete(role)
        log.append(f"role '{name}' deleted")
    db.flush()

    # 4. role whitelists inside ACL conditions
    for rule in db.query(ACLRule).order_by(ACLRule.resource_name).all():
        roles = (rule.conditions or {}).get("roles")
        if not roles:
            continue
        new_roles = []
        for entry in roles:
            replacement = rewrites.get(str(entry), entry)
            if replacement is None:
                log.append(f"ACCESS REMOVED: '{entry}' in conditions.roles of '{rule.resource_name}'")
            elif replacement != entry:
                log.append(f"conditions.roles of '{rule.resource_name}': '{entry}' -> '{replacement}'")
            if replacement is not None and replacement not in new_roles:
                new_roles.append(replacement)
        if new_roles != list(roles):
            # Reassign rather than mutate: a JSON column only notices a new object.
            rule.conditions = {**rule.conditions, "roles": new_roles}

    # 5. accounts without any role
    for account in db.query(User).order_by(User.username).all():
        if not account.roles:
            account.roles.append(user_role)
            log.append(f"user '{account.username}': (no role) -> {USER}")

    db.flush()
    return log


def obsolete_tables(bind):
    """The obsolete tables that still exist, in drop order."""
    existing = set(inspect(bind).get_table_names())
    return [name for name in OBSOLETE_TABLES if name in existing]


def drop_obsolete_tables(bind):
    """Drop the unused permission tables; return the names dropped."""
    dropped = obsolete_tables(bind)
    with bind.begin() as connection:
        for name in dropped:
            connection.execute(text(f"DROP TABLE {name}"))
    return dropped


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        bind = db.get_bind()
        # Decided before the session opens a transaction, so the inspection
        # does not contend with it.
        tables = obsolete_tables(bind)
        try:
            log = migrate(db)
        except Exception:
            db.rollback()
            raise

        for line in log:
            print(f"  {line}")
        for name in tables:
            print(f"  table '{name}' dropped")
        if not log and not tables:
            print("Nothing to do: roles already match the built-in set.")
            db.rollback()
            return

        if args.apply:
            db.commit()
            drop_obsolete_tables(bind)
            print(f"\nApplied {len(log) + len(tables)} change(s).")
        else:
            db.rollback()
            print(f"\nDry run: {len(log) + len(tables)} change(s) NOT written. Re-run with --apply.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
