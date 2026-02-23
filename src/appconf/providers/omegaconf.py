from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from .base import ConfigProvider
from ..omegaconf import OmegaConfigLoader, OmegaConfig


class OmegaConfProvider(ConfigProvider):
    """Config provider backed by OmegaConf. Supports get, set, and save."""

    def __init__(self, config_path: Path | str):
        self._config = OmegaConfig(OmegaConfigLoader.load_raw(config_path))
        self._config_path = Path(config_path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default=default)

    def set(self, key: str, value: Any) -> None:
        self._config.set(key, value)

    def save(self, path: Path | str | None = None) -> None:
        save_path = Path(path) if path is not None else self._config_path
        OmegaConf.save(self._config._config, save_path)

    def __contains__(self, key: str) -> bool:
        return key in self._config

    def __str__(self) -> str:
        return str(self._config)

    def __repr__(self) -> str:
        return f"OmegaConfProvider({self._config_path!r})"
