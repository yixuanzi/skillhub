"""Script to create the system_audit_logs table."""
from database import engine, Base
from models.system_audit_log import SystemAuditLog


def create_table():
    """Create the system_audit_logs table."""
    print("Creating system_audit_logs table...")
    Base.metadata.create_all(bind=engine, tables=[SystemAuditLog.__table__])
    print("system_audit_logs table created successfully!")


if __name__ == "__main__":
    create_table()
