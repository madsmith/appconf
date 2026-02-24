from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class Bind(Generic[T]):
    """Descriptor that binds a property to a config path with argparse override support.

    Use Bind[T] to declare the type that accessing this property will return.
    This enables type checkers to infer the correct type at access sites
    (e.g. cfg.save_dir is Path | None). Converter correctness is the caller's
    responsibility.

    Resolution order when accessed on an AppConfig instance:
    1. Local set-cache (if a value was explicitly assigned via __set__)
    2. Higher-priority providers (e.g. argparse)
    3. Backing store provider (e.g. OmegaConf/YAML)
    4. Bind default

    The set-cache ensures that an explicit assignment (cfg.port = 9090)
    is immediately visible on the next read, even if a higher-priority
    provider would otherwise shadow the backing store value.
    """

    def __init__(
        self,
        config_path: str,
        *,
        arg_key: str | None = None,
        action: str | None = None,
        converter: Callable[[Any], Any] | None = None,
        default: T | None = None,
    ):
        """
        config_path: Access path in the OmegaConfig
        arg_key: Name of the argparse argument to use for the value (defaults to the property name)
        """
        self.config_path: str = config_path
        self.arg_key: str | None = arg_key
        self.property_name: str | None = None
        self.action: str | None = action
        self.converter: Callable[[Any], Any] | None = converter
        self.default: T | None = default
        # Per-instance cache for values set via __set__. Keyed by id(instance)
        # so a single Bind descriptor (shared across all instances of a class)
        # keeps separate cached values per instance. Uses a WeakValueDictionary
        # pattern via _cache_attr on the instance to avoid preventing GC.
        self._cache_attr: str | None = None

    def __set_name__(self, owner, name: str) -> None:
        self.property_name = name
        self._cache_attr = f"_bind_cache_{name}"
        # Short hand, assume arg key is the same as property name if not specified
        if self.arg_key is None:
            self.arg_key = name

    def __get__(self, instance, owner) -> T | None:
        if instance is None:
            return self  # type: ignore[return-value]
        # Check per-instance set-cache first
        if self._cache_attr is not None:
            try:
                return object.__getattribute__(instance, self._cache_attr)
            except AttributeError:
                pass
        return instance._resolve_bind(self)

    def __set__(self, instance, value) -> None:
        instance.set(self.config_path, value)
        # Cache the value on the instance so the next __get__ returns it
        # immediately, bypassing provider resolution.
        if self._cache_attr is not None:
            object.__setattr__(instance, self._cache_attr, value)


class BindDefault(Bind[T]):
    """Bind variant whose __get__ returns T instead of T | None.

    Use when a default is guaranteed and you don't want None in the
    type signature. Requires a default value.
    """

    def __init__(
        self,
        config_path: str,
        *,
        default: T,
        arg_key: str | None = None,
        action: str | None = None,
        converter: Callable[[Any], Any] | None = None,
    ):
        super().__init__(
            config_path,
            arg_key=arg_key,
            action=action,
            converter=converter,
            default=default,
        )

    def __get__(self, instance, owner) -> T:
        if instance is None:
            return self  # type: ignore[return-value]
        if self._cache_attr is not None:
            try:
                return object.__getattribute__(instance, self._cache_attr)
            except AttributeError:
                pass
        return instance._resolve_bind(self)
