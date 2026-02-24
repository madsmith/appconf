from pathlib import Path

import pytest
from omegaconf import OmegaConf

from appconf import OmegaConfig, OmegaConfigLoader


@pytest.fixture
def simple_config():
    return OmegaConf.create(
        {
            "foo": "bar",
            "number": 42,
            "nested": {
                "key1": "value1",
                "key2": 123,
            },
        }
    )


@pytest.fixture
def config_with_defaults():
    return OmegaConf.create(
        {
            "foo": "bar",
            "nested": {
                "key1": "value1",
            },
        }
    )


def list_config_fixture():
    return OmegaConf.create(
        {
            "toplist": [
                {"innerdict": {"x": 1, "y": [10, 20, 30]}},
                {"innerdict": {"x": 2, "y": [40, 50]}},
            ],
            "dictlist": {
                "alist": [100, 200, {"foo": "bar"}],
                "nested": [{"a": [1, 2]}, {"b": [3, 4]}],
            },
        }
    )


# --- get ---


def test_get_top_level_key(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.get("foo") == "bar"
    assert cfg.get("number") == 42


def test_get_nested_key(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.get("nested.key1") == "value1"
    assert cfg.get("nested.key2") == 123


def test_missing_key_returns_none(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.get("does_not_exist") is None
    assert cfg.get("nested.nope") is None


def test_missing_key_with_default(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.get("does_not_exist", "default") == "default"
    assert cfg.get("nested.nope", 999) == 999


# --- __contains__ ---


def test_contains_existing_key(simple_config):
    cfg = OmegaConfig(simple_config)
    assert "foo" in cfg
    assert "nested.key1" in cfg


def test_contains_missing_key(simple_config):
    cfg = OmegaConfig(simple_config)
    assert "does_not_exist" not in cfg
    assert "nested.nope" not in cfg


def test_contains_none_value():
    cfg = OmegaConfig(OmegaConf.create({"key": None}))
    assert "key" in cfg


# --- __getattr__ / __setattr__ ---


def test_getattr_access(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.foo == "bar"
    assert cfg.number == 42


def test_getattr_missing_key(simple_config):
    cfg = OmegaConfig(simple_config)
    assert cfg.not_a_key is None


def test_getattr_access_and_setattr():
    cfg = OmegaConfig(OmegaConf.create({"foo": "bar"}))
    assert cfg.foo == "bar"
    cfg.newattr = 123
    assert cfg.get("newattr") == 123
    cfg.foo = "baz"
    assert cfg.foo == "baz"


def test_getattr_private_raises():
    cfg = OmegaConfig(OmegaConf.create({"foo": "bar"}))
    with pytest.raises(AttributeError):
        _ = cfg._nonexistent


# --- set ---


def test_set_top_level_key(simple_config):
    cfg = OmegaConfig(simple_config)
    cfg.set("new_key", "new_value")
    assert cfg.get("new_key") == "new_value"


def test_set_nested_key(simple_config):
    cfg = OmegaConfig(simple_config)
    cfg.set("nested.key3", "val3")
    assert cfg.get("nested.key3") == "val3"


def test_overwrite_existing_key(simple_config):
    cfg = OmegaConfig(simple_config)
    cfg.set("foo", "baz")
    assert cfg.get("foo") == "baz"


def test_set_new_nested_key(simple_config):
    cfg = OmegaConfig(simple_config)
    cfg.set("newparent.child", 123)
    assert cfg.get("newparent.child") == 123


def test_set_list_index():
    cfg = OmegaConfig(list_config_fixture())
    cfg.set("dictlist.alist.0", 111)
    assert cfg.get("dictlist.alist.0") == 111
    cfg.set("dictlist.alist.2.foo", "baz")
    assert cfg.get("dictlist.alist.2.foo") == "baz"


def test_set_nested_list_in_dict():
    cfg = OmegaConfig(list_config_fixture())
    cfg.set("toplist.0.innerdict.y.1", 77)
    assert cfg.get("toplist.0.innerdict.y.1") == 77
    cfg.set("toplist.1.innerdict.y.1", 88)
    assert cfg.get("toplist.1.innerdict.y.1") == 88


def test_set_dict_in_list_of_dicts():
    cfg = OmegaConfig(list_config_fixture())
    cfg.set("toplist.1.innerdict.z", 999)
    assert cfg.get("toplist.1.innerdict.z") == 999


def test_set_list_in_list_of_dicts():
    cfg = OmegaConfig(list_config_fixture())
    cfg.set("toplist.0.innerdict.newlist", [1, 2, 3])
    assert cfg.get("toplist.0.innerdict.newlist.2") == 3


def test_alternating_dict_list_set():
    cfg = OmegaConfig(list_config_fixture())
    cfg.set("dictlist.nested.1.b.0", 42)
    assert cfg.get("dictlist.nested.1.b.0") == 42
    cfg.set("toplist.0.innerdict.y.2", 12345)
    assert cfg.get("toplist.0.innerdict.y.2") == 12345


# --- __str__ / __repr__ ---


def test_str_and_repr():
    cfg = OmegaConfig(OmegaConf.create({"foo": "bar", "nested": {"x": 1}}))
    s = str(cfg)
    assert "foo" in s
    assert "bar" in s

    r = repr(cfg)
    assert "OmegaConfig" in r
    assert "foo" in r


# --- __init__ validation ---


def test_init_rejects_non_config():
    with pytest.raises(
        AssertionError, match="Config must be a DictConfig or ListConfig"
    ):
        OmegaConfig({"foo": "bar"})


# --- OmegaConfigLoader ---


def test_loader_load_basic(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar\nnumber: 42\n")

    cfg = OmegaConfigLoader.load(config_file)
    assert isinstance(cfg, OmegaConfig)
    assert cfg.foo == "bar"
    assert cfg.number == 42


def test_loader_load_merges_private(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar\nnumber: 42\n")
    private_file = tmp_path / "config_private.yaml"
    private_file.write_text("secret: shh\nnumber: 99\n")

    cfg = OmegaConfigLoader.load(config_file)
    assert cfg.foo == "bar"
    assert cfg.number == 99
    assert cfg.secret == "shh"


def test_loader_load_strips_private_key(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar\nprivate:\n  secret: shh\n")

    cfg = OmegaConfigLoader.load(config_file)
    assert cfg.foo == "bar"
    assert "private" not in cfg


def test_loader_load_raw(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar\n")

    raw = OmegaConfigLoader.load_raw(config_file)
    assert not isinstance(raw, OmegaConfig)
    assert raw.foo == "bar"


def test_loader_load_string_path(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar\n")

    cfg = OmegaConfigLoader.load(str(config_file))
    assert cfg.foo == "bar"


def test_loader_load_resolves_interpolations(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("base: hello\nderived: ${base}_world\n")

    cfg = OmegaConfigLoader.load(config_file)
    assert cfg.derived == "hello_world"
