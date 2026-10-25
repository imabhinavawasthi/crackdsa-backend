import time
import threading
import logging
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import inspect

logger = logging.getLogger(__name__)


class CacheEntry:
    __slots__ = ("value", "expires_at", "namespace", "created_at")

    def __init__(self, value: Any, ttl: int, namespace: str):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl > 0 else float("inf")
        self.namespace = namespace

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class InMemoryCacheManager:
    """
    High-performance, thread-safe, in-memory cache manager supporting TTL,
    namespaces, granular invalidation, and metrics.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, CacheEntry] = {}
        self._namespace_index: Dict[str, set] = {}
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                self._delete_key_locked(key)
                self._misses += 1
                return None

            self._hits += 1
            return entry.value

    DEFAULT_TTL: int = 86400  # 24 hours default in seconds

    def set(self, key: str, value: Any, ttl: int = 86400, namespace: str = "default") -> None:
        with self._lock:
            # If key already exists in a different namespace, remove from old index
            if key in self._store:
                old_ns = self._store[key].namespace
                if old_ns in self._namespace_index:
                    self._namespace_index[old_ns].discard(key)

            entry = CacheEntry(value=value, ttl=ttl, namespace=namespace)
            self._store[key] = entry

            if namespace not in self._namespace_index:
                self._namespace_index[namespace] = set()
            self._namespace_index[namespace].add(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._delete_key_locked(key)

    def _delete_key_locked(self, key: str) -> bool:
        entry = self._store.pop(key, None)
        if entry:
            if entry.namespace in self._namespace_index:
                self._namespace_index[entry.namespace].discard(key)
            return True
        return False

    def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidates all keys associated with a specific namespace.
        Returns the number of keys invalidated.
        """
        with self._lock:
            keys_to_delete = list(self._namespace_index.get(namespace, set()))
            count = 0
            for key in keys_to_delete:
                if self._delete_key_locked(key):
                    count += 1
            if namespace in self._namespace_index:
                self._namespace_index[namespace].clear()
            logger.info(f"[CacheManager] Invalidated namespace '{namespace}': {count} keys removed")
            return count

    def clear_all(self) -> int:
        """Flushes the entire in-memory cache."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._namespace_index.clear()
            logger.info(f"[CacheManager] Cleared entire cache: {count} keys removed")
            return count

    def purge_expired(self) -> int:
        """Cleans up expired keys to prevent memory creep."""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._store.items() if v.expires_at <= now]
            for key in expired_keys:
                self._delete_key_locked(key)
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Provides cache diagnostics and breakdown for the admin portal."""
        with self._lock:
            self.purge_expired()
            total_requests = self._hits + self._misses
            hit_rate = round((self._hits / total_requests * 100), 1) if total_requests > 0 else 0.0

            ns_breakdown = {}
            for ns, keys in self._namespace_index.items():
                active_count = sum(1 for k in keys if k in self._store)
                if active_count > 0:
                    ns_breakdown[ns] = active_count

            detailed_keys = []
            now = time.time()
            for k, entry in self._store.items():
                detailed_keys.append({
                    "key": k,
                    "namespace": entry.namespace,
                    "ttl_remaining_seconds": max(0, int(entry.expires_at - now)) if entry.expires_at != float("inf") else -1,
                    "created_at": int(entry.created_at),
                })

            return {
                "total_keys": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": hit_rate,
                "namespaces": ns_breakdown,
                "keys": detailed_keys[:100],  # cap for response size
            }


# Global singleton instance
cache_manager = InMemoryCacheManager()


def cached(
    namespace: str = "default",
    ttl: int = 86400,
    key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator for caching sync or async function results.
    Usage:
        @cached(namespace="courses", ttl=600)
        def get_course_detail(slug: str):
            ...
    """
    def decorator(func: Callable):
        func_name = f"{func.__module__}.{func.__qualname__}"

        def _build_default_key(*args, **kwargs) -> str:
            # Simple deterministic key from func name and string representations of args
            arg_strs = [str(a) for a in args]
            kwarg_strs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
            parts = [func_name] + arg_strs + kwarg_strs
            return ":".join(parts)

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = key_builder(*args, **kwargs) if key_builder else _build_default_key(*args, **kwargs)
                cached_val = cache_manager.get(key)
                if cached_val is not None:
                    return cached_val

                result = await func(*args, **kwargs)
                if result is not None:
                    cache_manager.set(key, result, ttl=ttl, namespace=namespace)
                return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = key_builder(*args, **kwargs) if key_builder else _build_default_key(*args, **kwargs)
                cached_val = cache_manager.get(key)
                if cached_val is not None:
                    return cached_val

                result = func(*args, **kwargs)
                if result is not None:
                    cache_manager.set(key, result, ttl=ttl, namespace=namespace)
                return result

            return sync_wrapper

    return decorator
