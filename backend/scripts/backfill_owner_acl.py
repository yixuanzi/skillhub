#!/usr/bin/env python3
"""Backfill resource owners into their ACL users whitelist.

Invocation permission is now decided purely by the ACL: ownership grants
management rights, not execute rights (ACLResourceService.enforce_permission).
New resources are created with the owner already seeded into
conditions["users"], but resources created before that change have an empty
RBAC rule, which now means "nobody may call this" - including their owner.

This script adds each resource's owner username to its ACL rule's users
whitelist. It only ever ADDS the owner; it never removes an existing entry,
never touches roles or role bindings, and never changes access_mode. Rules
already in ANY mode are left alone since they already allow everyone.

Usage:
    python scripts/backfill_owner_acl.py            # dry run, prints the plan
    python scripts/backfill_owner_acl.py --apply    # write the changes
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal  # noqa: E402
from models.acl import ACLRule, AccessMode  # noqa: E402
from models.resource import Resource  # noqa: E402
from models.user import User  # noqa: E402


def plan(db):
    """Return [(resource, rule, owner_username, new_users)] for rules needing a change."""
    changes = []
    for resource in db.query(Resource).order_by(Resource.name).all():
        rule = db.query(ACLRule).filter(ACLRule.resource_id == resource.id).first()
        if rule is None:
            changes.append((resource, None, None, None))  # reported, not fixed
            continue
        if rule.access_mode == AccessMode.ANY:
            continue
        if not resource.owner_id:
            continue
        owner = db.query(User).filter(User.id == resource.owner_id).first()
        if owner is None:
            continue

        users = list((rule.conditions or {}).get("users") or [])
        if owner.username in users:
            continue
        changes.append((resource, rule, owner.username, users + [owner.username]))
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        changes = plan(db)
        if not changes:
            print("Nothing to do: every resource's owner is already whitelisted.")
            return 0

        missing_rule = [c for c in changes if c[1] is None]
        to_update = [c for c in changes if c[1] is not None]

        for resource, _rule, owner_username, new_users in to_update:
            print(f"  {resource.name:30s} ({resource.type.value:8s})  users -> {new_users}")
        for resource, _r, _o, _n in missing_rule:
            print(f"  {resource.name:30s} has NO ACL rule at all - it is uncallable; "
                  "create one via the ACL API")

        if not args.apply:
            print(f"\nDry run: {len(to_update)} rule(s) would be updated. "
                  "Re-run with --apply to write.")
            return 0

        for _resource, rule, _owner_username, new_users in to_update:
            conditions = dict(rule.conditions or {})
            conditions["users"] = new_users
            # Reassign so SQLAlchemy sees the JSON column as dirty.
            rule.conditions = conditions
        db.commit()
        print(f"\nUpdated {len(to_update)} ACL rule(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
