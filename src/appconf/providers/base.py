from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..bind import Bind


class DefaultedValue:
    """Wrapper that marks a default value so it can be distinguished
    from an explicitly-provided value during resolution.

    Renders as the original value for argparse help strings (%(default)s).
    AppConfig._resolve_bind treats DefaultedValue as unresolved — it keeps
    consulting providers and only unwraps it as a last resort.
    """

    value: Any

    def __init__(self, value: Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return repr(self.value)


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for config providers. Providers supply values by key."""

    def bind_key(self, bind: Bind[Any]) -> str | None: ...
    def get(self, key: str) -> Any: ...


@runtime_checkable
class BackingStore(ConfigProvider, Protocol):
    """Protocol for providers that also support writes and persistence."""

    def set(self, key: str, value: Any) -> None: ...
    def save(self, path: Path | str | None = None) -> None: ...
    def __contains__(self, key: str) -> bool: ...
