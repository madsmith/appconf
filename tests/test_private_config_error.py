import argparse
from typing import final

import pytest

from appconf import AppConfig, Bind, PrivateConfigError


def test_missing_private_file_raises_private_config_error(tmp_path):
    """Config referencing ${private.x} without a companion _private.yaml raises PrivateConfigError."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("api_key: ${private.secrets.api_key}\n")

    @final
    class MyConfig(AppConfig):
        api_key = Bind[str]("api_key")

    with pytest.raises(PrivateConfigError, match="private.secrets.api_key") as exc_info:
        MyConfig(config_file, argparse.Namespace())

    err = exc_info.value
    assert err.key == "private.secrets.api_key"
    assert "was not found" in str(err)


def test_incomplete_private_file_raises_private_config_error(tmp_path):
    """Companion _private.yaml exists but is missing the referenced key."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("api_key: ${private.secrets.api_key}\n")

    private_file = tmp_path / "config_private.yaml"
    private_file.write_text("private:\n  other: value\n")

    @final
    class MyConfig(AppConfig):
        api_key = Bind[str]("api_key")

    with pytest.raises(PrivateConfigError, match="private.secrets.api_key") as exc_info:
        MyConfig(config_file, argparse.Namespace())

    err = exc_info.value
    assert "is missing key" in str(err)


def test_non_private_interpolation_error_not_caught(tmp_path):
    """InterpolationKeyError for non-private keys is not wrapped."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("value: ${nonexistent.key}\n")

    @final
    class MyConfig(AppConfig):
        value = Bind[str]("value")

    with pytest.raises(Exception, match="nonexistent.key"):
        MyConfig(config_file, argparse.Namespace())


def test_valid_private_config_loads(tmp_path):
    """Config with properly defined private keys loads successfully."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("api_key: ${private.secrets.api_key}\n")

    private_file = tmp_path / "config_private.yaml"
    private_file.write_text("private:\n  secrets:\n    api_key: my-secret\n")

    @final
    class MyConfig(AppConfig):
        api_key = Bind[str]("api_key")

    cfg = MyConfig(config_file, argparse.Namespace())
    assert cfg.api_key == "my-secret"
