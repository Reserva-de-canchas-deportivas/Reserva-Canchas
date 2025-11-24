import time
from typing import Dict


class InMemoryTokenBlacklist:
    def __init__(self) -> None:
        # Store jti -> exp_timestamp
        self._store: Dict[str, int] = {}

    def add(self, jti: str, exp_timestamp: int) -> None:
        self._store[jti] = exp_timestamp

    def contains(self, jti: str) -> bool:
        # Cleanup expired entries lazily
        now = int(time.time())
        expired = [key for key, exp in self._store.items() if exp <= now]
        for key in expired:
            self._store.pop(key, None)

        exp = self._store.get(jti)
        return exp is not None and exp > now


blacklist = InMemoryTokenBlacklist()
