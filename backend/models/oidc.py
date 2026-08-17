"""Persistence models for the SkillHub Aegis Portal OIDC client."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OidcLoginTransaction(Base):
    """Short-lived server-side state for direct launch and SSO requests."""

    __tablename__ = "oidc_login_transactions"
    __table_args__ = (
        Index("ix_oidc_login_transaction_expires_at", "expires_at"),
    )

    state = Column(String(128), primary_key=True)
    nonce = Column(String(128), nullable=False)
    code_verifier = Column(String(256), nullable=False)
    client_id = Column(String(255), nullable=False)
    organization_id = Column(String(36), nullable=True)
    flow = Column(String(16), nullable=False, default="sso")
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class SsoLoginTicket(Base):
    """One-time exchange ticket kept as a digest, never as a bearer token."""

    __tablename__ = "sso_login_tickets"
    __table_args__ = (
        Index("ix_sso_login_ticket_user_id", "user_id"),
        Index("ix_sso_login_ticket_expires_at", "expires_at"),
    )

    ticket_digest = Column(String(64), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
