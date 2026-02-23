import argparse
from pathlib import Path
from typing import Any

from omegaconf import ListConfig

from .bind import Bind
from .providers.argparse import ArgNamespaceProvider
from .providers.omegaconf import OmegaConfProvider


class AppConfig:
    """Config backed by providers with Bind descriptor support.

    Providers are consulted in priority order during Bind resolution.
    The OmegaConf provider serves as the backing store for get/set/save.
    """

    def __init__(
        self,
        config_path: Path | str,
        args: argparse.Namespace | None = None,
        arg_defaults: dict[str, Any] | None = None,
    ):
        self._store = OmegaConfProvider(config_path)
        self._providers = []

        if args is not None:
            self._providers.append(ArgNamespaceProvider(args, arg_defaults))

        self._providers.append(self._store)

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default=default)

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)

    def save(self, path: Path | str | None = None) -> None:
        self._store.save(path)

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def _resolve_bind(self, bind: Bind) -> Any:
        resolved = False
        r_value = None

        for provider in self._providers:
            if isinstance(provider, ArgNamespaceProvider):
                key = bind.arg_key
                if key is None:
                    continue
            else:
                key = bind.config_path

            value = provider.get(key)
            if value is not None:
                if r_value is None:
                    r_value = value
                    resolved = bind.action != "append"
                elif (
                    bind.action == "append"
                    and isinstance(r_value, list)
                ):
                    if isinstance(value, (list, ListConfig)):
                        r_value.extend(value)
                    else:
                        r_value.append(value)
                    resolved = True
                else:
                    # Already have a value and not append — skip
                    continue

        if not resolved and r_value is None and bind.default is not None:
            r_value = bind.default

        if bind.converter is not None and r_value is not None:
            if isinstance(r_value, (list, ListConfig)):
                r_value = [bind.converter(v) for v in r_value]
            else:
                r_value = bind.converter(r_value)

        return r_value

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        # Check for Bind descriptor on the class — delegate to its __set__
        for cls in type(self).__mro__:
            if name in cls.__dict__:
                attr = cls.__dict__[name]
                if isinstance(attr, Bind):
                    attr.__set__(self, value)
                    return
                break

        self.set(name, value)

    def __str__(self) -> str:
        return str(self._store)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._store!r})"
