import argparse
from typing import final

from appconf import AppConfig, Bind, BindDefault
from appconf.providers.base import DefaultedValue

# --- Bind descriptor ---


def test_bind_set_name():
    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    bind = MyConfig.__dict__["port"]
    assert bind.property_name == "port"
    assert bind.arg_key == "port"


def test_bind_explicit_arg_key():
    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port", arg_key="server_port")

    bind = MyConfig.__dict__["port"]
    assert bind.arg_key == "server_port"


def test_bind_class_access_returns_descriptor():
    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    assert isinstance(MyConfig.port, Bind)


def test_bind_set_writes_through_to_config_path(tmp_path):
    """Assignment on a Bind property writes through to the backing store
    at the bound config_path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args)
    cfg.port = 9090
    assert cfg.port == 9090


def test_bind_set_cache_overrides_arg_provider(tmp_path):
    """After an explicit set, the cached value wins over a higher-priority provider."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace(port=5000)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 5000  # args wins before set
    cfg.port = 9090
    assert cfg.port == 9090  # set-cache wins after set


# --- AppConfig resolution order ---


def test_resolve_argparse_wins(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace(port=9090)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 9090


def test_resolve_config_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 8080


def test_resolve_bind_default(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port", default=3000)

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 3000


def test_resolve_defaulted_value_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace(port=DefaultedValue(5000))
    cfg = MyConfig(config_file, args)
    assert cfg.port == 5000


def test_resolve_bind_defaults_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args, bind_defaults={"port": 5000})
    assert cfg.port == 5000


def test_resolve_bind_defaults_below_yaml(tmp_path):
    """YAML config wins over bind_defaults."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args, bind_defaults={"port": 5000})
    assert cfg.port == 8080


def test_resolve_none_when_nothing_matches(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args)
    assert cfg.port is None


# --- Converter ---


def test_resolve_with_converter(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: '8080'\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port", converter=int)

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 8080
    assert isinstance(cfg.port, int)


def test_resolve_converter_with_list(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("paths:\n  - '1'\n  - '2'\n  - '3'\n")

    @final
    class MyConfig(AppConfig):
        paths = Bind[list[int]]("paths", converter=int)

    args = argparse.Namespace(paths=None)
    cfg = MyConfig(config_file, args)
    assert cfg.paths == [1, 2, 3]


# --- Append action ---


def test_resolve_append_merges(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("extra:\n  - from_config\n")

    @final
    class MyConfig(AppConfig):
        items = Bind[list[str]]("extra", arg_key="items", action="append")

    args = argparse.Namespace(items=["from_arg"])
    cfg = MyConfig(config_file, args)
    # append: arg value present but action=append means not fully resolved,
    # so config gets appended
    assert cfg.items == ["from_arg", "from_config"]


# --- Non-Bind attribute storage ---


def test_non_bind_attr_is_normal_python_attr(tmp_path):
    """Setting a non-Bind attribute stores it as a normal instance attribute,
    not in the backing store."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = Bind[int]("server.port")

    cfg = MyConfig(config_file)
    cfg.local_value = 42
    assert cfg.local_value == 42  # type: ignore[assign]
    assert "local_value" in cfg.__dict__


# --- BindDefault ---


def test_bind_default_resolves_from_default(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    @final
    class MyConfig(AppConfig):
        port = BindDefault[int]("server.port", default=3000)

    cfg = MyConfig(config_file)
    assert cfg.port == 3000


def test_bind_default_resolves_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = BindDefault[int]("server.port", default=3000)

    cfg = MyConfig(config_file)
    assert cfg.port == 8080


def test_bind_default_set_cache(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    @final
    class MyConfig(AppConfig):
        port = BindDefault[int]("server.port", default=3000)

    cfg = MyConfig(config_file)
    cfg.port = 9090
    assert cfg.port == 9090


def test_bind_default_is_bind_subclass():
    assert issubclass(BindDefault, Bind)


def test_bind_default_class_access_returns_descriptor():
    @final
    class MyConfig(AppConfig):
        port = BindDefault[int]("server.port", default=3000)

    assert isinstance(MyConfig.port, BindDefault)
