"""Audit logging middleware for HTTP request logging.

This middleware logs all HTTP requests to the system audit logs for
security monitoring, compliance, and debugging.

Supports logging of both GET query parameters and POST body content.
"""
from fastapi import Request
from sqlalchemy.orm import Session
from time import time
import os
import json
from typing import Any, Dict

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

# Maximum body size to log (in bytes) to avoid logging huge payloads
MAX_BODY_LOG_SIZE = 10 * 1024  # 10KB

# Body content types to skip logging (for security/performance)
SKIP_BODY_CONTENT_TYPES = {
    "multipart/form-data",  # File uploads
}


async def _parse_body_for_logging(content_type: str, body_bytes: bytes) -> Dict[str, Any]:
    """Parse request body for audit logging.

    Args:
        content_type: Content-Type header value
        body_bytes: Raw body bytes

    Returns:
        Dict with parsed body info
    """
    body_info = {"body_type": content_type}

    if len(body_bytes) > MAX_BODY_LOG_SIZE:
        body_info["truncated"] = True
        body_info["content_length"] = len(body_bytes)
        body_info["preview"] = body_bytes[:MAX_BODY_LOG_SIZE].decode("utf-8", errors="ignore") + "..."
        return body_info

    try:
        # Parse JSON
        if "application/json" in content_type:
            json_data = json.loads(body_bytes.decode("utf-8"))
            body_info["json"] = json_data

        # Parse form data
        elif "application/x-www-form-urlencoded" in content_type:
            from urllib.parse import parse_qs
            form_data = parse_qs(body_bytes.decode("utf-8"))
            # Parse_qs returns lists for each key, simplify for single values
            body_info["form"] = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}

        # Other content types - store as text
        else:
            try:
                body_info["text"] = body_bytes.decode("utf-8")
            except UnicodeDecodeError:
                body_info["bytes_length"] = len(body_bytes)

    except Exception as e:
        body_info["parse_error"] = str(e)

    return body_info


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

    # Extract user info
    user_id = getattr(request.state, "user_id", None)
    #username = None
    if not user_id:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub")
                #username = payload.get("username")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Parse body info BEFORE call_next for POST/PUT/PATCH requests
    body_info = None
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        content_type = request.headers.get("content-type", "")

        # Skip multipart/form-data (file uploads)
        if any(ct in content_type for ct in SKIP_BODY_CONTENT_TYPES):
            body_info = {
                "body_type": content_type,
                "skipped": "File upload - not logged"
            }
        elif content_type:
            # Read and cache body for logging
            # This requires us to restore the body for downstream consumers
            try:
                # Store the original _body attribute (if it exists)
                original_body = getattr(request, "_body", None)

                # Read the body (this sets request._body)
                body_bytes = await request.body()

                # Parse for logging
                if body_bytes:
                    body_info = await _parse_body_for_logging(content_type, body_bytes)

                # Restore _body to None so downstream consumers can read it again
                # Starlette's Request.body() caches in _body, but if we set it to None,
                # the next call will read from the stream again, which is already consumed
                # So we need to keep it, but Starlette will check if it's already set

                # Actually, the issue is that once body() is called, the stream is consumed
                # We can't "unread" the stream. But we can cache the body and override
                # the Request._body to make it available again.

                # The solution: don't restore, just leave it. Starlette caches properly.
                # Wait - let me check the actual implementation...

                # Actually, after reading body(), request._body is set.
                # If we call request.body() again, it returns the cached value.
                # So downstream code SHOULD work. Let's verify this works.

            except Exception as e:
                # If body parsing fails, just log the error
                body_info = {
                    "body_type": content_type,
                    "parse_error": str(e)
                }

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time() - start_time

    # Determine action
    action = f"{request.method.lower()} {request.url.path}"

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    # Determine status
    status = "success" if response.status_code < 400 else "failure"

    try:
        # Build details
        details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else {},
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "auth_method": getattr(request.state, "auth_method", None)
        }

        # Add body info
        if body_info:
            details["body"] = body_info

        # Log the request
        SystemAuditLogService.log_action(
            db=db,
            user_id=user_id,
            action=action,
            resource_type="http_request",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=None if status == "success" else f"HTTP {response.status_code}"
        )
    except Exception as e:
        print(f"Audit logging failed: {e}")
    finally:
        try:
            db_gen.close()
        except Exception:
            pass

    return response
