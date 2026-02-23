import argparse
from typing import Any

from .base import ConfigProvider


class _DefaultsExtractor:
    """Extracts and suppresses argparse defaults.

    This is used internally to separate argparse defaults from explicitly-provided
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


class ArgNamespaceProvider(ConfigProvider):
    """Config provider that reads from a pre-parsed argparse Namespace and defaults dict."""

    def __init__(
        self,
        args: argparse.Namespace,
        defaults: dict[str, Any] | None = None,
    ):
        self._args = args
        self._defaults = defaults or {}

    def get(self, key: str) -> Any:
        # Explicit arg value takes priority
        if hasattr(self._args, key):
            value = getattr(self._args, key)
            if value is not None:
                return value

        # Fall back to defaults
        value = self._defaults.get(key)
        if value is not None:
            return value

        return None


class ArgParseProvider(ArgNamespaceProvider):
    """Config provider that takes an ArgumentParser, extracts defaults, parses args,
    and merges in any additional defaults."""

    def __init__(
        self,
        parser: argparse.ArgumentParser,
        defaults: dict[str, Any] | None = None,
    ):
        extracted = _DefaultsExtractor(parser).extract()
        merged = extracted | (defaults or {})
        args = parser.parse_args()
        super().__init__(args, merged)
