"""Audit logging middleware for HTTP request logging.

This middleware logs all HTTP requests to the system audit logs for
security monitoring, compliance, and debugging.
"""
from fastapi import Request
from sqlalchemy.orm import Session
from time import time
import os

from database import get_db
from services.system_audit_log_service import SystemAuditLogService
from core.security import verify_token
from core.deps import get_current_user

# Environment configuration
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"

# Paths to exclude from audit logging (health checks, etc.)
EXCLUDED_PATHS = {
    "/health",
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
}


async def audit_middleware(request: Request, call_next):
    """Log all HTTP requests to audit logs.

    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler

    Returns:
        HTTP response
    """
    # Skip audit logging if disabled or for excluded paths
    if not AUDIT_LOG_ENABLED or request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    start_time = time()

    # Extract user_id from request.state (set by get_current_user if already executed)
    # or from Authorization header (for middleware execution)
    user_id = getattr(request.state, "user_id", None)

    # If user_id not in state, try to extract from Authorization header
    if not user_id:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            # Try JWT token
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub")
                username=payload.get("username")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time() - start_time

    # Determine action from method + path
    action = f"{request.method.lower()} {request.url.path}"

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    # Determine status based on response code
    status = "success" if response.status_code < 400 else "failure"

    try:
        # Log the request
        SystemAuditLogService.log_action(
            db=db,
            user_id=username,
            action=action,
            resource_type="http_request",
            details={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "auth_method": getattr(request.state, "auth_method", None)
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=None if status == "success" else f"HTTP {response.status_code}"
        )
    except Exception as e:
        # Don't fail the request if logging fails
        # Just log the error (in production, use proper logging)
        print(f"Audit logging failed: {e}")
    finally:
        # Always close the database session
        try:
            db_gen.close()
        except Exception:
            pass

    return response
