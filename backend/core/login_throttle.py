"""Slow down password guessing on the login endpoint.

Failed logins are counted in a sliding window, per username and per client IP:

- per username (case-insensitive): stops someone working through passwords for
  one account, from however many addresses.
- per IP: stops one client working through many accounts. The limit is higher,
  because a whole office can sit behind one address.

While either count is at its limit, login attempts for that username / from
that address are refused with 429 before the password is even checked - a
correct password does not get through either, otherwise the limit would only
slow down wrong guesses. A successful login clears the username's count.

State lives in this process's memory. That is enough for the single-worker
deployment this app ships with; with several workers each keeps its own count,
so the effective limit is multiplied by the number of workers, and a restart
clears it. Move it to shared storage before scaling out.
"""
import threading
import time
from collections import deque
from typing import Callable, Deque, Dict, Optional, Tuple

from config import settings

# Upper bound on tracked keys, so made-up usernames cannot grow this forever.
MAX_TRACKED_KEYS = 10000

Key = Tuple[str, str]


class LoginThrottle:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._failures: Dict[Key, Deque[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _limits() -> Dict[str, int]:
        return {"user": settings.LOGIN_MAX_FAILURES, "ip": settings.LOGIN_MAX_FAILURES_PER_IP}

    @staticmethod
    def _keys(username: Optional[str], ip: Optional[str]):
        if username:
            yield ("user", username.strip().lower())
        if ip:
            yield ("ip", ip)

    def _recent(self, key: Key, now: float) -> Deque[float]:
        """This key's failures inside the window (older ones are dropped)."""
        failures = self._failures.get(key)
        if failures is None:
            return deque()
        cutoff = now - settings.LOGIN_FAILURE_WINDOW_SECONDS
        while failures and failures[0] <= cutoff:
            failures.popleft()
        if not failures:
            del self._failures[key]
        return failures

    def retry_after(self, username: Optional[str], ip: Optional[str]) -> int:
        """Seconds until this username/IP may try again; 0 if it may try now."""
        now = self._clock()
        wait = 0.0
        with self._lock:
            for key in self._keys(username, ip):
                limit = self._limits()[key[0]]
                if limit <= 0:
                    continue
                failures = self._recent(key, now)
                if len(failures) >= limit:
                    # Blocked until the oldest of the last `limit` failures ages out.
                    oldest = failures[len(failures) - limit]
                    wait = max(wait, oldest + settings.LOGIN_FAILURE_WINDOW_SECONDS - now)
        return int(wait) + 1 if wait > 0 else 0

    def record_failure(self, username: Optional[str], ip: Optional[str]) -> None:
        now = self._clock()
        with self._lock:
            for key in self._keys(username, ip):
                if self._limits()[key[0]] <= 0:
                    continue
                self._recent(key, now)
                self._failures.setdefault(key, deque()).append(now)
            if len(self._failures) > MAX_TRACKED_KEYS:
                self._evict(now)

    def record_success(self, username: Optional[str]) -> None:
        """A correct password clears the account's count (not the IP's)."""
        with self._lock:
            for key in self._keys(username, None):
                self._failures.pop(key, None)

    def _evict(self, now: float) -> None:
        for key in list(self._failures):
            self._recent(key, now)
        # Still too many live keys: drop the ones whose last failure is oldest.
        overflow = len(self._failures) - MAX_TRACKED_KEYS
        if overflow > 0:
            for key in sorted(self._failures, key=lambda k: self._failures[k][-1])[:overflow]:
                del self._failures[key]

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = LoginThrottle()
