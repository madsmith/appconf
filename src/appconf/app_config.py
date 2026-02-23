import argparse
from pathlib import Path
from typing import Any

from omegaconf import ListConfig

from .bind import Bind
from .providers.argparse import ArgNamespaceProvider
from .providers.base import BackingStore, DefaultedValue
from .providers.omegaconf import OmegaConfProvider


class AppConfig:
    """Config backed by providers with Bind descriptor support.

    Providers are consulted in priority order during Bind resolution.
    The provider satisfying BackingStore is used for writes and persistence.
    """

    def __init__(
        self,
        config_path: Path | str,
        args: argparse.Namespace | None = None,
        bind_defaults: dict[str, Any] | None = None,
    ):
        self._providers = []
        self._bind_defaults = bind_defaults or {}

        if args is not None:
            self._providers.append(ArgNamespaceProvider(args))

        self._providers.append(OmegaConfProvider(config_path))

    @property
    def _store(self) -> BackingStore:
        for provider in self._providers:
            if isinstance(provider, BackingStore):
                return provider
        raise RuntimeError("No backing store found among providers")

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)

    def save(self, path: Path | str | None = None) -> None:
        self._store.save(path)

    def _resolve_bind(self, bind: Bind) -> Any:
        # Resolution order:
        #   1. Set-cache (handled by Bind.__get__ before we get here)
        #   2. Explicit arg value
        #   3. YAML config
        #   4. bind_defaults (by property name)
        #   5. Bind default
        #   6. DefaultedValue (unwrapped)
        #   7. None
        result = None
        defaulted = None

        for provider in self._providers:
            key = provider.bind_key(bind)
            if key is None:
                continue

            value = provider.get(key)
            if value is None:
                continue

            if isinstance(value, DefaultedValue):
                defaulted = defaulted or value.value
                continue

            if result is None:
                result = value
            elif bind.action == "append" and isinstance(result, list):
                if isinstance(value, (list, ListConfig)):
                    result.extend(value)
                else:
                    result.append(value)

        if result is None:
            result = (
                self._bind_defaults.get(bind.property_name)
                if bind.property_name is not None
                else None
            )

        if result is None:
            if bind.default is not None:
                result = bind.default
            elif defaulted is not None:
                result = defaulted

        return self._convert(result, bind)

    @staticmethod
    def _convert(value: Any, bind: Bind) -> Any:
        if bind.converter is not None and value is not None:
            if isinstance(value, (list, ListConfig)):
                return [bind.converter(v) for v in value]
            return bind.converter(value)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        # Because we override __setattr__, Python no longer auto-dispatches to
        # data descriptors (classes with __get__/__set__) like Bind.  We need to
        # manually walk the MRO (Method Resolution Order — the chain of classes
        # Python searches: MyConfig → AppConfig → object) to find if this name
        # is a Bind descriptor, and if so, call its __set__ which writes through
        # to the backing store via config_path.
        #
        # The `break` after a non-Bind match stops the search: if something
        # named e.g. 'port' exists on a parent class but isn't a Bind, we stop
        # and fall through to normal attribute storage.
        for cls in type(self).__mro__:
            if name in cls.__dict__:
                attr = cls.__dict__[name]
                if isinstance(attr, Bind):
                    attr.__set__(self, value)
                    return
                break

        # Not a Bind — normal Python attribute storage.
        super().__setattr__(name, value)

    def _resolved_binds(self) -> dict[str, Any]:
        binds: dict[str, Bind] = {}
        for klass in reversed(type(self).__mro__):
            for name, attr in klass.__dict__.items():
                if isinstance(attr, Bind):
                    binds[name] = attr
        return {name: self._resolve_bind(bind) for name, bind in binds.items()}

    def __str__(self) -> str:
        return str(self._resolved_binds())

    def __repr__(self) -> str:
        parts = [f"{k}={v!r}" for k, v in self._resolved_binds().items()]

        providers = []
        for p in self._providers:
            name = type(p).__name__
            if isinstance(p, BackingStore):
                name += "*"
            providers.append(name)

        parts.append(f"providers=[{', '.join(providers)}]")
        return f"{type(self).__name__}({', '.join(parts)})"
