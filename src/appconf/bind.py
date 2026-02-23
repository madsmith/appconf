from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class Bind(Generic[T]):
    """Descriptor that binds a property to a config path with argparse override support.

    Use Bind[T] to declare the type that accessing this property will return.
    This enables type checkers to infer the correct type at access sites
    (e.g. cfg.save_dir is Path | None). Converter correctness is the caller's
    responsibility.

    Resolution order when accessed on an AppConfig instance:
    1. Argparse value (if provided and not None)
    2. Config file value (via config_path)
    3. Bind default
    4. Argparse parser default (from arg_defaults)
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

    def __set_name__(self, owner, name: str) -> None:
        self.property_name = name
        # Short hand, assume arg key is the same as property name if not specified
        if self.arg_key is None:
            self.arg_key = name

    def __get__(self, instance, owner) -> T | None:
        if instance is None:
            return self  # type: ignore[return-value]
        return instance._resolve_bind(self)

    def __set__(self, instance, value) -> None:
        raise AttributeError(
            f"'{self.property_name}' is read-only; "
            f"modify '{self.config_path}' via config.set(...) instead"
        )
