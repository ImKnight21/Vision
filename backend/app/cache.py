"""In-process TTL cache with single-flight.

Upstream APIs are rate-limited, so two things matter: reuse a fresh answer, and
never fire the same request twice concurrently. A plain dict handles the first;
the per-key lock handles the second, which is what actually saves us when a
dashboard mounts and ten widgets ask for the same series at once.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()

    def _get_fresh(self, key: str, now: float) -> tuple[bool, Any]:
        entry = self._entries.get(key)
        if entry is not None and entry.expires_at > now:
            return True, entry.value
        return False, None

    async def _lock_for(self, key: str) -> asyncio.Lock:
        async with self._guard:
            return self._locks.setdefault(key, asyncio.Lock())

    async def get_or_set(
        self, key: str, ttl: int, producer: Callable[[], Awaitable[T]]
    ) -> T:
        """Return the cached value, or produce and store it under `key`."""
        now = time.monotonic()
        hit, value = self._get_fresh(key, now)
        if hit:
            return value

        lock = await self._lock_for(key)
        async with lock:
            # Someone may have filled the entry while we waited for the lock.
            hit, value = self._get_fresh(key, time.monotonic())
            if hit:
                return value

            produced = await producer()
            self._entries[key] = _Entry(
                value=produced, expires_at=time.monotonic() + ttl
            )
            return produced

    def invalidate(self, prefix: str = "") -> int:
        """Drop entries whose key starts with `prefix`. Empty prefix clears all."""
        doomed = [k for k in self._entries if k.startswith(prefix)]
        for key in doomed:
            del self._entries[key]
        return len(doomed)

    def stats(self) -> dict[str, int]:
        now = time.monotonic()
        live = sum(1 for e in self._entries.values() if e.expires_at > now)
        return {"entries": len(self._entries), "live": live}


cache = TTLCache()
