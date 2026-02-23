import argparse
from pathlib import Path
from typing import Any

from omegaconf import ListConfig

from .bind import Bind
from .omega_config import OmegaConfig
from .loader import OmegaConfigLoader


class DefaultsExtractor:
    """Extracts and suppresses argparse defaults.

    This is used to separate argparse defaults from explicitly-provided
    arguments, allowing the resolution order in Bind to work correctly.
    """

    def __init__(self, parser: argparse.ArgumentParser):
        self._parser = parser

    def extract(self) -> dict[str, Any]:
        defaults = {}

        for action in self._parser._actions:
            if (
                action.dest != argparse.SUPPRESS
                and action.default is not argparse.SUPPRESS
            ):
                defaults[action.dest] = action.default
                action.default = argparse.SUPPRESS

        return defaults


class AppConfig(OmegaConfig):
    """Config that merges argparse arguments with YAML config via Bind descriptors."""

    def __init__(
        self,
        config_path: Path | str,
        args: argparse.Namespace | None = None,
        arg_defaults: dict[str, Any] | None = None,
    ):
        super().__init__(OmegaConfigLoader.load_raw(config_path))

        self._args = args
        self._arg_defaults = arg_defaults

    def _resolve_bind(self, bind: Bind) -> Any:
        resolved = False
        r_value = None

        if self._args is not None:
            arg_key = bind.arg_key
            if arg_key and hasattr(self._args, arg_key):
                value = getattr(self._args, arg_key)
                if value is not None:
                    r_value = value
                    resolved = True and bind.action != "append"

        value = self.get(bind.config_path)
        if not resolved and value is not None:
            if (
                r_value is not None
                and bind.action == "append"
                and isinstance(r_value, list)
            ):
                r_value.extend(value)
            else:
                r_value = value
            resolved = True

        if bind.default:
            if not resolved and bind.default and not r_value:
                r_value = bind.default
                resolved = True

        if self._arg_defaults and bind.arg_key is not None:
            value = self._arg_defaults.get(bind.arg_key)
            if not resolved and value and not r_value:
                r_value = value
                resolved = True

        if bind.converter is not None and r_value is not None:
            if isinstance(r_value, (list, ListConfig)):
                r_value = [bind.converter(v) for v in r_value]
            else:
                r_value = bind.converter(r_value)

        return r_value
