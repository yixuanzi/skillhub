"""Composio integration service.

Wraps three Composio meta tools behind SkillHub's single, globally-configured
`composio` resource:
- COMPOSIO_SEARCH_TOOLS: search the Composio catalog for relevant tools
- COMPOSIO_GET_TOOL_SCHEMAS: fetch full input schemas for tool slugs
- COMPOSIO_MULTI_EXECUTE_TOOL: execute one or more discovered tools

The resource row itself is a system-wide singleton (enforced in ResourceService),
but its credentials are NOT necessarily shared: `ext` supports the same
`{token_name}` managed-token placeholders as gateway/third resources, resolved
against the *calling* user's own tokens (see GatewayService._replace_token_placeholders).
So `ext.COMPOSIO_API_KEY = "{my_composio_key}"` makes every user execute as their
own Composio account, while a literal value makes everyone share one account.

Because of that, the client/session cache is keyed per
(resource name, SkillHub user id) - never by resource alone - so one user's
resolved token can never be reused for another user.

COMPOSIO_SEARCH_TOOLS and COMPOSIO_GET_TOOL_SCHEMAS can run through direct
execution (composio.tools.execute), but COMPOSIO_MULTI_EXECUTE_TOOL is rejected
by Composio's API unless it runs inside a Tool Router session
(composio.sessions.create(...).execute(...)) - confirmed empirically, not just
documented. See docs/composio-meta-tools-exploration.md for the full writeup.
"""
import asyncio
import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.resource import Resource, ResourceType
from models.user import User
from schemas.resource import ComposioConfig
from core.exceptions import ValidationException, ExternalServiceException
from config import settings

logger = logging.getLogger(__name__)


class ComposioService:
    """Service for calling Composio's meta tools via the singleton `composio` resource."""

    # Cache of {"client": Composio, "session": ToolRouterSession | None, "created_at": float},
    # keyed by "{resource_name}::{skillhub_user_id}".
    _session_cache: Dict[str, Dict[str, Any]] = {}

    # One lock per cache key so a slow session handshake for one user doesn't
    # block another. Creating/looking up a lock here never awaits, so no guard is
    # needed around this dict on asyncio's single-threaded event loop.
    _key_locks: Dict[str, asyncio.Lock] = {}

    @staticmethod
    def _cache_key(resource_name: str, user_id: str) -> str:
        return f"{resource_name}::{user_id}"

    @staticmethod
    def _get_key_lock(cache_key: str) -> asyncio.Lock:
        lock = ComposioService._key_locks.get(cache_key)
        if lock is None:
            lock = asyncio.Lock()
            ComposioService._key_locks[cache_key] = lock
        return lock

    @staticmethod
    def _is_expired(entry: Dict[str, Any]) -> bool:
        ttl = settings.COMPOSIO_SESSION_TTL_SECONDS
        if ttl <= 0:
            return False
        return (time.monotonic() - entry["created_at"]) > ttl

    @staticmethod
    def _evict_if_needed() -> None:
        """Drop the oldest entries once the cache exceeds its configured size."""
        max_entries = settings.COMPOSIO_SESSION_MAX_ENTRIES
        overflow = len(ComposioService._session_cache) - max_entries
        if max_entries <= 0 or overflow <= 0:
            return

        oldest_keys = sorted(
            ComposioService._session_cache.keys(),
            key=lambda k: ComposioService._session_cache[k]["created_at"],
        )[:overflow]
        for key in oldest_keys:
            ComposioService._drop_key(key)

    @staticmethod
    def _drop_key(cache_key: str) -> None:
        ComposioService._session_cache.pop(cache_key, None)
        lock = ComposioService._key_locks.get(cache_key)
        if lock is not None and not lock.locked():
            ComposioService._key_locks.pop(cache_key, None)

    @staticmethod
    def invalidate_resource(resource_name: str) -> None:
        """Drop every cached client/session for this resource, across all users.

        Synchronous and safe to call from non-async code (e.g. resource
        update/delete in ResourceService): the dict/lock mutations here contain
        no ``await`` points. Call this whenever the composio resource's `ext`
        (API key, user id, token placeholders) or name changes, or it is
        deleted - otherwise a stale client keeps using the old credentials
        until the TTL expires.
        """
        prefix = f"{resource_name}::"
        stale_keys = [k for k in ComposioService._session_cache if k.startswith(prefix)]
        for key in stale_keys:
            ComposioService._drop_key(key)
        if stale_keys:
            logger.info(
                f"Invalidated {len(stale_keys)} cached composio client(s) for resource: {resource_name}"
            )

    @staticmethod
    def get_cached_keys() -> list[str]:
        """Cache keys ("{resource_name}::{user_id}") with live clients/sessions."""
        return list(ComposioService._session_cache.keys())

    @staticmethod
    def get_singleton_resource(db: Session) -> Resource:
        """Find the one composio-type resource, if any.

        Raises:
            ValidationException: If no composio resource has been configured yet
        """
        resource = db.query(Resource).filter(Resource.type == ResourceType.COMPOSIO).first()
        if not resource:
            raise ValidationException(
                "No composio resource is configured. Create one (type=composio) with "
                "ext.COMPOSIO_API_KEY and ext.COMPOSIO_USER_ID first."
            )
        return resource

    @staticmethod
    def _resolve_config(db: Session, resource: Resource, user_id: str) -> ComposioConfig:
        """Parse `ext` into a config, resolving {token_name} against this user's tokens."""
        if not resource.ext:
            raise ValidationException(
                "composio resource is missing ext.COMPOSIO_API_KEY / ext.COMPOSIO_USER_ID"
            )

        from services.gateway_service import GatewayService
        from services.mtoken_service import MTokenService

        mtokens = MTokenService.list_all(db, user_id, limit=1000)
        # Fails closed on unknown placeholders ("Token not found: x") rather than
        # sending a literal "{my_key}" to Composio as an API key.
        resolved = GatewayService._replace_token_placeholders(db, user_id, resource.ext, mtokens)

        try:
            return ComposioConfig(**resolved)
        except Exception as e:
            raise ValidationException(f"Invalid composio resource config: {e}")

    @staticmethod
    def _authorize(db: Session, user: User) -> tuple[Resource, ComposioConfig]:
        """Resolve the singleton resource + this user's effective config, ACL-checked."""
        from services.acl_resource_service import ACLResourceService

        resource = ComposioService.get_singleton_resource(db)
        # Invocation permission is ACL-only, exactly as for gateway/third/mcp.
        ACLResourceService.enforce_permission(db, resource.id, user, resource.name)
        return resource, ComposioService._resolve_config(db, resource, str(user.id))

    @staticmethod
    def _build_client(config: ComposioConfig):
        try:
            from composio import Composio
        except ImportError:
            raise ExternalServiceException(
                "composio package is required. Install it with: pip install composio"
            )
        return Composio(api_key=config.COMPOSIO_API_KEY)

    @staticmethod
    async def _get_entry(resource_name: str, config: ComposioConfig, user_id: str) -> Dict[str, Any]:
        """Get (or create) the cached client entry for this (resource, user)."""
        cache_key = ComposioService._cache_key(resource_name, user_id)
        lock = ComposioService._get_key_lock(cache_key)

        async with lock:
            entry = ComposioService._session_cache.get(cache_key)
            if entry is not None and not ComposioService._is_expired(entry):
                return entry

            entry = {
                "client": ComposioService._build_client(config),
                "session": None,
                "created_at": time.monotonic(),
            }
            ComposioService._session_cache[cache_key] = entry
            ComposioService._evict_if_needed()
            logger.info(f"Created composio client for resource={resource_name} user={user_id}")
            return entry

    @staticmethod
    async def _get_session(resource_name: str, config: ComposioConfig, user_id: str):
        """Get (or lazily create) this (resource, user)'s tool-router session."""
        cache_key = ComposioService._cache_key(resource_name, user_id)
        entry = await ComposioService._get_entry(resource_name, config, user_id)
        lock = ComposioService._get_key_lock(cache_key)

        async with lock:
            if entry["session"] is None:
                client = entry["client"]
                entry["session"] = await asyncio.to_thread(
                    lambda: client.sessions.create(user_id=config.COMPOSIO_USER_ID)
                )
                logger.info(
                    f"Created composio tool-router session for resource={resource_name} user={user_id}"
                )
            return entry["session"]

    @staticmethod
    async def search_tools(
        db: Session,
        user: User,
        use_case: str,
        known_fields: Optional[str] = None,
    ) -> dict:
        """Call COMPOSIO_SEARCH_TOOLS for a single natural-language use case."""
        resource, config = ComposioService._authorize(db, user)
        entry = await ComposioService._get_entry(resource.name, config, str(user.id))

        query: dict[str, Any] = {"use_case": use_case}
        if known_fields:
            query["known_fields"] = known_fields

        def _run():
            return entry["client"].tools.execute(
                "COMPOSIO_SEARCH_TOOLS",
                user_id=config.COMPOSIO_USER_ID,
                arguments={"queries": [query]},
                dangerously_skip_version_check=True,
            )

        try:
            return await asyncio.to_thread(_run)
        except Exception as e:
            raise ExternalServiceException(f"Composio search failed: {_describe(e)}")

    @staticmethod
    async def get_tool_schemas(db: Session, user: User, tool_slugs: list[str]) -> dict:
        """Call COMPOSIO_GET_TOOL_SCHEMAS for one or more tool slugs."""
        resource, config = ComposioService._authorize(db, user)
        entry = await ComposioService._get_entry(resource.name, config, str(user.id))

        def _run():
            return entry["client"].tools.execute(
                "COMPOSIO_GET_TOOL_SCHEMAS",
                user_id=config.COMPOSIO_USER_ID,
                arguments={"tool_slugs": tool_slugs},
                dangerously_skip_version_check=True,
            )

        try:
            return await asyncio.to_thread(_run)
        except Exception as e:
            raise ExternalServiceException(f"Composio get_tool_schemas failed: {_describe(e)}")

    @staticmethod
    async def multi_execute_tool(db: Session, user: User, tools: list[dict]) -> dict:
        """Call COMPOSIO_MULTI_EXECUTE_TOOL with one or more {tool_slug, arguments}.

        Must run inside a Tool Router session - Composio's API rejects this
        specific meta tool on the direct-execution path regardless of API key
        permissions. The session is cached per (resource, user); if a cached one
        has gone stale server-side the call is retried once with a fresh session.
        """
        resource, config = ComposioService._authorize(db, user)
        user_id = str(user.id)

        arguments = {
            "tools": tools,
            "sync_response_to_workbench": False,
            "memory": {},
        }

        last_error: Optional[Exception] = None
        for attempt in (1, 2):
            session = await ComposioService._get_session(resource.name, config, user_id)
            try:
                result = await asyncio.to_thread(
                    lambda: session.execute("COMPOSIO_MULTI_EXECUTE_TOOL", arguments=arguments)
                )
                return result.model_dump() if hasattr(result, "model_dump") else result
            except Exception as e:
                last_error = e
                if attempt == 1:
                    # Session may have expired server-side - drop it and retry once.
                    logger.warning(
                        f"composio exec failed (attempt 1), retrying with a fresh session: {e}"
                    )
                    ComposioService._drop_key(ComposioService._cache_key(resource.name, user_id))
                    continue

        raise ExternalServiceException(f"Composio multi_execute_tool failed: {_describe(last_error)}")


def _describe(exc: Optional[BaseException]) -> str:
    """Render an exception with its underlying cause.

    Composio's SDK raises APIConnectionError whose str() is just
    "Connection error." - the actual reason (TLS verification failure, DNS,
    timeout) only lives on __cause__, so include it or every network problem
    looks identical in the API response.
    """
    if exc is None:
        return "unknown error"
    text = str(exc) or exc.__class__.__name__
    cause = exc.__cause__ or exc.__context__
    if cause is not None:
        cause_text = str(cause) or cause.__class__.__name__
        if cause_text and cause_text not in text:
            return f"{text} ({cause.__class__.__name__}: {cause_text})"
    return text
