#!/usr/bin/env python3
"""Redact secrets from audit log rows written before redaction existed.

The audit middleware used to store request bodies verbatim, so
`system_audit_logs.details` contains login passwords, managed token values,
resource credentials and refresh tokens in clear text. New rows are redacted as
they are written (core/redaction.py); this script applies the same redaction to
the rows already in the database.

Only `details` is rewritten, and only where redaction changes it: the row, its
timestamp, user, action and status are kept, so the audit trail stays intact.
On SQLite the database is vacuumed afterwards, because an UPDATE leaves the old
values in free pages of the file until then.

Rewriting the rows does not un-leak what was stored: anyone who could read the
audit log, a database backup or a copy of the file may have seen those values.
Passwords and tokens that appear in the report should be changed.

Usage:
    python scripts/redact_audit_logs.py            # dry run, prints the plan
    python scripts/redact_audit_logs.py --apply    # write the changes
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from core.redaction import redact_request  # noqa: E402
from database import SessionLocal  # noqa: E402
from models.system_audit_log import SystemAuditLog  # noqa: E402

BATCH_SIZE = 500


def _path_of(log: SystemAuditLog) -> str:
    """The request path a row was logged for (`action` is "<method> <path>")."""
    details = log.details if isinstance(log.details, dict) else {}
    path = details.get("path")
    if path:
        return path
    return log.action.split(" ", 1)[1] if log.action and " " in log.action else ""


def redact_logs(db) -> Counter:
    """Redact every row in `db`'s open transaction; return {action: rows changed}.

    Does not commit - the caller commits to apply, or rolls back for a dry run.
    """
    changed = Counter()
    last_id = ""
    while True:
        batch = (
            db.query(SystemAuditLog)
            .filter(SystemAuditLog.id > last_id)
            .order_by(SystemAuditLog.id)
            .limit(BATCH_SIZE)
            .all()
        )
        if not batch:
            break
        for log in batch:
            if log.details is None:
                continue
            cleaned = redact_request(_path_of(log), log.details)
            if cleaned != log.details:
                # Reassign rather than mutate: a JSON column only notices a new object.
                log.details = cleaned
                changed[log.action] += 1
        last_id = batch[-1].id
        db.flush()
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total = db.query(SystemAuditLog).count()
        try:
            changed = redact_logs(db)
        except Exception:
            db.rollback()
            raise

        rows = sum(changed.values())
        for action, count in sorted(changed.items(), key=lambda item: (-item[1], item[0])):
            print(f"  {count:6d}  {action}")
        print(f"\n{rows} of {total} audit log row(s) contain values that need redacting.")
        if not rows:
            db.rollback()
            return

        if not args.apply:
            db.rollback()
            print("Dry run: nothing written. Re-run with --apply.")
            return

        db.commit()
        bind = db.get_bind()
        if bind.dialect.name == "sqlite":
            db.close()
            # VACUUM cannot run inside a transaction.
            with bind.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.execute(text("VACUUM"))
            print("Database vacuumed.")
        print(f"Redacted {rows} row(s). Change any password or token that was logged.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
