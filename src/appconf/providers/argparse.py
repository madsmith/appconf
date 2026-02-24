import argparse
from typing import Any, Generic, TypeVar

from ..bind import Bind
from .base import ConfigProvider, DefaultedValue

T = TypeVar("T")


class ArgParseWrapper:
    """Wraps an ArgumentParser's defaults with DefaultedValue markers
    so that AppConfig can distinguish explicit arguments from defaults."""

    @staticmethod
    def wrap(parser: argparse.ArgumentParser) -> None:
        """Wrap all argparse defaults with DefaultedValue markers.

        Call this before parse_args(). After parsing, arguments that still
        hold a DefaultedValue were not explicitly provided by the user.
        """
        for action in parser._actions:
            if (
                action.dest != argparse.SUPPRESS
                and action.default is not argparse.SUPPRESS
            ):
                action.default = DefaultedValue(action.default)


class ArgNamespaceProvider(ConfigProvider, Generic[T]):
    """Config provider that reads from a pre-parsed argparse Namespace.

    Returns values as-is, including DefaultedValue wrappers. Resolution
    logic in AppConfig handles unwrapping.
    """

    _args: argparse.Namespace

    def __init__(self, args: argparse.Namespace):
        self._args = args

    def bind_key(self, bind: Bind[T]) -> str | None:
        return bind.arg_key

    def get(self, key: str) -> Any:
        if hasattr(self._args, key):
            value = getattr(self._args, key)
            if value is not None:
                return value

        return None


class ArgParseProvider(ArgNamespaceProvider[T]):
    """Config provider that takes an ArgumentParser, marks defaults, parses args."""

    def __init__(self, parser: argparse.ArgumentParser):
        ArgParseWrapper.wrap(parser)
        args = parser.parse_args()
        super().__init__(args)
