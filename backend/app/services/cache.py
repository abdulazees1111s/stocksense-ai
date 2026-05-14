from datetime import datetime, timedelta
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._store: dict[str, tuple[datetime, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        created_at, value = item
        if datetime.utcnow() - created_at > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (datetime.utcnow(), value)

    def clear(self) -> None:
        self._store.clear()
