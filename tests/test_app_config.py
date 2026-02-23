import argparse

from appconf import AppConfig, Bind


# --- Bind descriptor ---

def test_bind_set_name():
    class MyConfig(AppConfig):
        port = Bind("server.port")

    bind = MyConfig.__dict__["port"]
    assert bind.property_name == "port"
    assert bind.arg_key == "port"


def test_bind_explicit_arg_key():
    class MyConfig(AppConfig):
        port = Bind("server.port", arg_key="server_port")

    bind = MyConfig.__dict__["port"]
    assert bind.arg_key == "server_port"


def test_bind_class_access_returns_descriptor():
    class MyConfig(AppConfig):
        port = Bind("server.port")

    assert isinstance(MyConfig.port, Bind)


def test_bind_set_writes_through_to_config_path(tmp_path):
    """Assignment on a Bind property writes through to the backing store
    at the bound config_path."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args)
    cfg.port = 9090
    assert cfg.port == 9090


# --- AppConfig resolution order ---

def test_resolve_argparse_wins(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    args = argparse.Namespace(port=9090)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 9090


def test_resolve_config_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 8080


def test_resolve_bind_default(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    class MyConfig(AppConfig):
        port = Bind("server.port", default=3000)

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 3000


def test_resolve_arg_defaults_fallback(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args, arg_defaults={"port": 5000})
    assert cfg.port == 5000


def test_resolve_none_when_nothing_matches(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: localhost\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    args = argparse.Namespace()
    cfg = MyConfig(config_file, args)
    assert cfg.port is None


# --- Converter ---

def test_resolve_with_converter(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: '8080'\n")

    class MyConfig(AppConfig):
        port = Bind("server.port", converter=int)

    args = argparse.Namespace(port=None)
    cfg = MyConfig(config_file, args)
    assert cfg.port == 8080
    assert isinstance(cfg.port, int)


def test_resolve_converter_with_list(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("paths:\n  - '1'\n  - '2'\n  - '3'\n")

    class MyConfig(AppConfig):
        paths = Bind("paths", converter=int)

    args = argparse.Namespace(paths=None)
    cfg = MyConfig(config_file, args)
    assert cfg.paths == [1, 2, 3]


# --- Append action ---

def test_resolve_append_merges(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("extra:\n  - from_config\n")

    class MyConfig(AppConfig):
        items = Bind("extra", arg_key="items", action="append")

    args = argparse.Namespace(items=["from_arg"])
    cfg = MyConfig(config_file, args)
    # append: arg value present but action=append means not fully resolved,
    # so config gets appended
    assert cfg.items == ["from_arg", "from_config"]


