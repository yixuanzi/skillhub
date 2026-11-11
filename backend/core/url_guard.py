"""Decide which URLs the server is willing to call on a user's behalf.

Any signed-in user can create a resource, point it at a URL and have the
gateway fetch that URL and hand back the response. Without a check that is a
server-side request forgery primitive: the "resource" can be the cloud metadata
endpoint, a database admin port on localhost or any service on the internal
network that trusts requests coming from this host.

The rule: a target is allowed when its address is publicly routable, or when an
administrator has listed it in `GATEWAY_ALLOWED_HOSTS`. Everything else -
loopback, private ranges, link-local (169.254.169.254), unique-local IPv6,
unspecified and reserved addresses - is refused.

`GATEWAY_ALLOWED_HOSTS` entries may be:
- a CIDR or single IP:       "10.20.0.0/16", "192.168.1.5"
- an exact hostname:         "billing.internal"
- a wildcard suffix:         "*.corp.example.com"
- "*" to switch the guard off entirely (development only)

Two checks, because a hostname can only be judged once it is resolved:
- `check_url` is synchronous and does no DNS. It runs when a resource is saved,
  so an obviously local target is rejected with a clear message up front.
- `ensure_url_allowed` also resolves the name and checks every address it maps
  to. It runs immediately before each outbound call, so a name that pointed
  somewhere harmless when the resource was saved is re-checked every time.

Known limit: the HTTP client resolves the name again when it connects, so a
DNS record that changes between the check and the connection (rebinding) is not
caught here. Redirects are not followed by the gateway, so a public URL cannot
bounce the request to an internal one.
"""
import asyncio
import ipaddress
import logging
import socket
from typing import List, Optional, Tuple
from urllib.parse import urlsplit

from config import settings
from core.exceptions import ValidationException

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = ("http", "https")

_NOT_ALLOWED = (
    "points to a local or private network address, which resources may not target. "
    "An administrator can allow it with GATEWAY_ALLOWED_HOSTS."
)


def _allowlist() -> Tuple[bool, list, set, list]:
    """Parse GATEWAY_ALLOWED_HOSTS into (allow_all, networks, hostnames, suffixes)."""
    allow_all, networks, hostnames, suffixes = False, [], set(), []
    for raw in settings.GATEWAY_ALLOWED_HOSTS or []:
        entry = str(raw).strip().lower()
        if not entry:
            continue
        if entry == "*":
            allow_all = True
        elif entry.startswith("*."):
            suffixes.append(entry[1:])  # keep the leading dot
        else:
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                hostnames.add(entry)
    return allow_all, networks, hostnames, suffixes


def _host_is_allowlisted(host: str) -> bool:
    allow_all, _, hostnames, suffixes = _allowlist()
    return allow_all or host in hostnames or any(host.endswith(suffix) for suffix in suffixes)


def _address_is_allowed(address: str) -> bool:
    """True when `address` is publicly routable or inside an allowlisted network."""
    allow_all, networks, _, _ = _allowlist()
    if allow_all:
        return True
    ip = ipaddress.ip_address(address)
    # ::ffff:10.0.0.1 is 10.0.0.1 as far as the network is concerned.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if any(ip.version == network.version and ip in network for network in networks):
        return True
    return ip.is_global


def _split(url: Optional[str], what: str) -> Tuple[str, Optional[int], str]:
    """Return (host, port, scheme) of `url`, rejecting anything that is not plain http(s)."""
    if not url or not str(url).strip():
        raise ValidationException(f"{what} is required")
    try:
        parts = urlsplit(str(url).strip())
        port = parts.port
    except ValueError:
        raise ValidationException(f"{what} is not a valid URL")
    scheme = (parts.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValidationException(f"{what} must start with http:// or https://")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise ValidationException(f"{what} is not a valid URL: it has no host")
    return host, port, scheme


def _literal_ip(host: str) -> Optional[str]:
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        return None


def check_url(url: Optional[str], what: str = "URL") -> None:
    """Reject `url` if it is plainly not allowed, without resolving DNS.

    Raises:
        ValidationException: bad scheme, no host, or a literal local/private target.
    """
    host, _, _ = _split(url, what)
    if _host_is_allowlisted(host):
        return
    literal = _literal_ip(host)
    if literal is not None:
        if not _address_is_allowed(literal):
            raise ValidationException(f"{what} {_NOT_ALLOWED}")
        return
    # Names that are local by definition, whatever the resolver says.
    if host == "localhost" or host.endswith(".localhost"):
        raise ValidationException(f"{what} {_NOT_ALLOWED}")


async def _resolve(host: str, port: Optional[int]) -> List[str]:
    """Every address `host` resolves to."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port or 0, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


async def ensure_url_allowed(url: Optional[str], what: str = "URL") -> None:
    """Reject `url` unless every address it resolves to may be called.

    Call this right before making the request.

    Raises:
        ValidationException: as `check_url`, plus an unresolvable name or a
            name that resolves to a local/private address.
    """
    check_url(url, what)
    host, port, _ = _split(url, what)
    if _host_is_allowlisted(host) or _literal_ip(host) is not None:
        return  # already decided by check_url

    try:
        addresses = await _resolve(host, port)
    except (socket.gaierror, OSError):
        raise ValidationException(f"{what} host '{host}' could not be resolved")
    if not addresses:
        raise ValidationException(f"{what} host '{host}' could not be resolved")

    blocked = [address for address in addresses if not _address_is_allowed(address)]
    if blocked:
        # The address stays in the server log: telling the caller would turn
        # this check into a way to map internal DNS.
        logger.warning("Blocked outbound request to %s: resolves to %s", host, ", ".join(blocked))
        raise ValidationException(f"{what} {_NOT_ALLOWED}")
