from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


class DefaultedValue(Generic[T]):
    """Wrapper that marks a default value so it can be distinguished
    from an explicitly-provided value during resolution.

    Renders as the original value for argparse help strings (%(default)s).
    AppConfig._resolve_bind treats DefaultedValue as unresolved — it keeps
    consulting providers and only unwraps it as a last resort.
    """

    value: T

    def __init__(self, value: T):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return repr(self.value)


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
