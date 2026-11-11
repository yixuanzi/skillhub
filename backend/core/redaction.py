"""Keep secrets out of the audit log.

The audit middleware records request bodies and query strings so that actions
can be reconstructed later. Those bodies carry passwords (login, register,
change-password, admin user management), managed token values, resource `ext`
configs with upstream credentials, refresh tokens and whatever a caller passes
to a gateway call. None of that may reach `system_audit_logs.details`, which
every admin can read.

`redact_request` is the one entry point: it takes what would be logged and
returns a copy with secrets replaced by `***`. It errs on the side of hiding
too much - a redacted harmless field costs nothing, a logged password does.
scripts/redact_audit_logs.py applies the same function to rows written before
this existed.
"""
import json
import re
from typing import Any, FrozenSet, Optional

REDACTED = "***"

# A key is sensitive when its name contains any of these (case-insensitive).
_SENSITIVE_PARTS = (
    "password", "passwd", "secret", "token", "authorization", "credential",
    "api_key", "apikey", "api-key", "private_key", "cookie",
)

# Keys whose whole subtree is credentials more often than not: every string
# under them is hidden, whatever its own key is called.
_OPAQUE_SUBTREES = frozenset({"headers", "ext"})

# Extra exact key names that are only secret on particular endpoints. `value`
# is a managed token's secret; `code`/`state`/`ticket` are OIDC login material.
_PATH_KEYS = (
    ("/api/v1/mtokens", frozenset({"value"})),
    ("/api/v1/sso", frozenset({"code", "state", "ticket"})),
)

# A string that is nothing but a `{name}` placeholder names a managed token
# rather than containing one, so it is safe (and useful) to keep.
_PLACEHOLDER_ONLY = re.compile(r"^\{[^{}]+\}$")


def is_sensitive_key(key: Any) -> bool:
    lowered = str(key).lower()
    return any(part in lowered for part in _SENSITIVE_PARTS)


def _hide(value: Any) -> Any:
    """Replace a secret, keeping "nothing was sent" distinguishable."""
    return value if value is None or value == "" else REDACTED


def _hide_leaves(value: Any) -> Any:
    """Hide every string in `value`, keeping its shape and pure placeholders."""
    if isinstance(value, dict):
        return {key: _hide_leaves(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_hide_leaves(item) for item in value]
    if isinstance(value, str):
        return value if value == "" or _PLACEHOLDER_ONLY.match(value) else REDACTED
    return value


def redact(value: Any, extra_keys: FrozenSet[str] = frozenset()) -> Any:
    """Return a copy of `value` with secrets replaced by `***`."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if is_sensitive_key(key) or lowered in extra_keys:
                result[key] = _hide(item)
            elif lowered in _OPAQUE_SUBTREES:
                result[key] = _hide_leaves(_parse_embedded_json(item))
            else:
                result[key] = redact(item, extra_keys)
        return result
    if isinstance(value, list):
        return [redact(item, extra_keys) for item in value]
    if isinstance(value, str):
        # Tool arguments are sometimes a JSON document passed as a string
        # (e.g. the MCP tools' `inputs`); look inside rather than trusting it.
        parsed = _parse_embedded_json(value)
        if parsed is not value:
            return json.dumps(redact(parsed, extra_keys), ensure_ascii=False)
    return value


def _parse_embedded_json(value: Any) -> Any:
    """Decode `value` if it is a string holding a JSON object/array, else return it as is."""
    if isinstance(value, str) and value[:1] in ("{", "["):
        try:
            parsed = json.loads(value)
        except ValueError:
            return value
        if isinstance(parsed, (dict, list)):
            return parsed
    return value


def _extra_keys_for(path: Optional[str]) -> FrozenSet[str]:
    path = path or ""
    for prefix, keys in _PATH_KEYS:
        if path.startswith(prefix):
            return keys
    return frozenset()


def redact_request(path: Optional[str], details: Any) -> Any:
    """Redact an audit `details` payload for a request to `path`.

    Besides key-based redaction this drops free-text copies of a body, which
    cannot be inspected field by field: the `preview` of an oversized body and
    the `text` of a body that is neither JSON nor a form.
    """
    if not isinstance(details, dict):
        return redact(details, _extra_keys_for(path))

    cleaned = redact(details, _extra_keys_for(path))
    body = cleaned.get("body")
    if isinstance(body, dict):
        for free_text in ("preview", "text"):
            if free_text in body:
                body.pop(free_text)
                body["omitted"] = "raw body not logged"
    return cleaned
