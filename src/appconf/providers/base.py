from typing import Any


class ConfigProvider:
    """Base class for config providers. Providers supply values by key."""

    def get(self, key: str) -> Any:
        raise NotImplementedError
