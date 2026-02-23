from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for config providers. Providers supply values by key."""

    def get(self, key: str) -> Any: ...


@runtime_checkable
class BackingStore(ConfigProvider, Protocol):
    """Protocol for providers that also support writes and persistence."""

    def set(self, key: str, value: Any) -> None: ...
    def save(self, path: Path | str | None = None) -> None: ...
    def __contains__(self, key: str) -> bool: ...
