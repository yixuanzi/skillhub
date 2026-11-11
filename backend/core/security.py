"""Security module for JWT token handling and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SECRET_KEY signs every access and refresh token: whoever knows it can mint a
# token for any user, including a super_admin. These are the values that ship
# in the repository and its docs, so they are public knowledge.
PLACEHOLDER_SECRET_KEYS = frozenset({
    "your-secret-key-change-in-production",
    "your-secret-key",
    "change-me",
    "changeme",
    "secret",
})
MIN_SECRET_KEY_LENGTH = 32


def ensure_secret_key_is_safe() -> None:
    """Refuse to serve with a SECRET_KEY that is a known placeholder or too short.

    Called once at startup. Raising here stops the server instead of letting it
    run with tokens anyone could forge.

    Raises:
        RuntimeError: If SECRET_KEY is unset, a shipped placeholder, or shorter
            than MIN_SECRET_KEY_LENGTH characters.
    """
    key = (settings.SECRET_KEY or "").strip()
    if key.lower() in PLACEHOLDER_SECRET_KEYS:
        problem = "is still the placeholder value from the repository"
    elif len(key) < MIN_SECRET_KEY_LENGTH:
        problem = f"is shorter than {MIN_SECRET_KEY_LENGTH} characters"
    else:
        return
    raise RuntimeError(
        f"Refusing to start: SECRET_KEY {problem}. It signs every login token, so "
        "anyone who knows it can sign in as any user. Set a private random value in "
        "the environment or .env, for example the output of:\n"
        '    python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to compare against

    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash of the password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict) -> str:
    """Create JWT access token.

    Args:
        data: Payload data to encode in token (e.g., user_id, username)

    Returns:
        Complete JWT access token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(data: Dict) -> str:
    """Create JWT refresh token.

    Args:
        data: Payload data to encode in token (e.g., user_id, username)

    Returns:
        Complete JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_token_last32(token: str) -> str:
    """Extract last 32 characters of token for response to client.

    Args:
        token: Complete JWT token

    Returns:
        Last 32 characters of the token
    """
    return token[-32:]


def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token and decode payload.

    Args:
        token: Complete JWT token (not truncated)

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        # Full token required for verification
        if len(token) == 32:
            # Truncated token - can't verify without full token
            raise JWTError("Truncated token - need full token for verification")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def verify_refresh_token(token_hash: str, db) -> Optional[Dict]:
    """Verify refresh token by looking up in database.

    Args:
        token_hash: Hash of the full refresh token
        db: Database session

    Returns:
        Decoded payload if valid and not expired, None otherwise
    """
    from models.user import RefreshToken

    # Look up token in database
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not refresh_token:
        return None

    # Check expiration
    if refresh_token.expires_at < datetime.now(timezone.utc):
        return None

    # Token is valid (note: we don't decode JWT here, just verify it exists and isn't expired)
    return {"user_id": refresh_token.user_id}
