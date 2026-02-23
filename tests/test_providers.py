import argparse
from pathlib import Path

from appconf import (
    AppConfig, Bind, ArgNamespaceProvider, ArgParseProvider, OmegaConfProvider,
)


# --- ArgNamespaceProvider ---

def test_arg_namespace_provider_get_from_args():
    args = argparse.Namespace(port=9090)
    provider = ArgNamespaceProvider(args)
    assert provider.get("port") == 9090


def test_arg_namespace_provider_get_from_defaults():
    args = argparse.Namespace()
    provider = ArgNamespaceProvider(args, defaults={"port": 8080})
    assert provider.get("port") == 8080


def test_arg_namespace_provider_args_wins_over_defaults():
    args = argparse.Namespace(port=9090)
    provider = ArgNamespaceProvider(args, defaults={"port": 8080})
    assert provider.get("port") == 9090


def test_arg_namespace_provider_none_arg_falls_to_default():
    args = argparse.Namespace(port=None)
    provider = ArgNamespaceProvider(args, defaults={"port": 8080})
    assert provider.get("port") == 8080


def test_arg_namespace_provider_missing_key_returns_none():
    args = argparse.Namespace()
    provider = ArgNamespaceProvider(args)
    assert provider.get("nonexistent") is None


# --- ArgParseProvider ---

def test_argparse_provider_extracts_defaults_and_parses(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--port", "9090"])

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="localhost")

    provider = ArgParseProvider(parser)

    # Explicit arg
    assert provider.get("port") == 9090
    # Extracted default (not provided on CLI)
    assert provider.get("host") == "localhost"


def test_argparse_provider_merges_extra_defaults(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)

    provider = ArgParseProvider(parser, defaults={"port": 5000, "extra": "val"})

    # Extra defaults override extracted parser defaults
    assert provider.get("port") == 5000
    assert provider.get("extra") == "val"


def test_argparse_provider_is_arg_namespace_provider():
    """ArgParseProvider is a subclass of ArgNamespaceProvider."""
    assert issubclass(ArgParseProvider, ArgNamespaceProvider)


# --- OmegaConfProvider ---

def test_omegaconf_provider_get(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    provider = OmegaConfProvider(config_file)
    assert provider.get("server.port") == 8080


def test_omegaconf_provider_set(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    provider = OmegaConfProvider(config_file)
    provider.set("server.port", 9090)
    assert provider.get("server.port") == 9090


def test_omegaconf_provider_contains(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    provider = OmegaConfProvider(config_file)
    assert "server.port" in provider
    assert "server.missing" not in provider


def test_omegaconf_provider_save_roundtrip(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    provider = OmegaConfProvider(config_file)
    provider.set("server.port", 9090)
    provider.save()

    # Reload and verify
    provider2 = OmegaConfProvider(config_file)
    assert provider2.get("server.port") == 9090


def test_omegaconf_provider_save_to_different_path(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")
    output_file = tmp_path / "output.yaml"

    provider = OmegaConfProvider(config_file)
    provider.set("server.port", 9090)
    provider.save(output_file)

    # Original unchanged
    provider_original = OmegaConfProvider(config_file)
    assert provider_original.get("server.port") == 8080

    # Output has new value
    provider_output = OmegaConfProvider(output_file)
    assert provider_output.get("server.port") == 9090


# --- AppConfig with no args (config-only) ---

def test_appconfig_no_args(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    cfg = MyConfig(config_file)
    assert cfg.port == 8080


# --- Bind write-through ---

def test_bind_write_through(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    cfg = MyConfig(config_file)
    cfg.port = 9090
    assert cfg.port == 9090


# --- Save via AppConfig ---

def test_appconfig_save(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 8080\n")

    class MyConfig(AppConfig):
        port = Bind("server.port")

    cfg = MyConfig(config_file)
    cfg.port = 9090
    cfg.save()

    # Reload and verify
    cfg2 = MyConfig(config_file)
    assert cfg2.port == 9090
