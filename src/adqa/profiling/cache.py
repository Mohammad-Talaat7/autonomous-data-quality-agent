from __future__ import annotations

from .models.profiling_result import ProfilingResult


class ProfileCache:
    """
    Simple in-memory profiling cache.
    """

    def __init__(self) -> None:
        self._store: dict[str, ProfilingResult] = {}

    def get(self, key: str) -> ProfilingResult | None:
        return self._store.get(key)

    def set(self, key: str, value: ProfilingResult) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()
