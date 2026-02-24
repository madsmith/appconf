# appconf

Typed application config with YAML files and argparse override support, powered by [OmegaConf](https://github.com/omry/omegaconf).

Declare config properties as `Bind` descriptors on an `AppConfig` subclass.  Application can pass around a typed config object that resolves its values from a sequence of providers such as argparse or a YAML backing store.

## Install

```
uv pip install appconf
```

## Usage

Given a YAML config file (`config.yaml`):

```yaml
server:
  host: localhost
  port: 8080
  debug: false
```

Define your config class:

```python
from appconf import AppConfig, Bind, BindDefault

class ServerConfig(AppConfig):
    host = BindDefault[str]("server.host", default="0.0.0.0")
    port = BindDefault[int]("server.port", converter=int, default=3000)
    debug = Bind[bool]("server.debug")
```

`BindDefault` requires a `default` and narrows the return type to `T` instead of `T | None`, so type checkers know the value is never `None`. Use `Bind` when the property may legitimately be unset.

And use it in your application:

```python
from appconf.providers.argparse import ArgParseWrapper

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default=8080)
parser.add_argument("--debug", action="store_true")

# Important: call before parse_args() to annotate defaults
ArgParseWrapper.wrap(parser)
args = parser.parse_args()

cfg = ServerConfig("config.yaml", args)

print(cfg.host)   # "localhost"  (from YAML)
print(cfg.port)   # 8080         (from YAML, converted to int)
print(cfg.debug)  # False        (from YAML)
```

`ArgParseWrapper.wrap()` annotates defaults such that resolution of properties
can fall through to other providers. If not called, then argparse would resolve
every property that has a default specified.

## Resolution Order

Parameter resolution occurs in the following order:

1. Command-line arguments parsed by argparse
2. YAML config properties
3. Default values
    1. `bind_defaults` passed to AppConfig constructor
    2. argparse defaults (wrapped by `ArgParseWrapper`)
    3. `Bind` descriptor defaults

## Writing and Saving

```python
cfg.port = 9090           # writes to YAML backing store + local cache
cfg.save()                # persists to the original file
cfg.save("backup.yaml")   # or to a different path
```

## Converters

Apply a converter to transform the resolved value. YAML values are often strings — converters let you work with proper types:

```python
from pathlib import Path

class MyConfig(AppConfig):
    save_dir = BindDefault[Path]("app.save_dir", default=Path("."), converter=Path)
    tags = Bind[list[str]]("tags", converter=str.upper)
```

```yaml
app:
  save_dir: ~/output
tags:
  - hello
  - world
```

```python
cfg.save_dir  # Path("~/output")
cfg.tags      # ["HELLO", "WORLD"]
```

When the resolved value is a list, the converter is applied to each element.

## Append action

Merge list values from argparse and the config file:

```python
class MyConfig(AppConfig):
    plugins = Bind[list[str]]("plugins", action="append")
```

```yaml
plugins:
  - from_config
```

```
$ python app.py --plugins from_arg
# cfg.plugins == ["from_arg", "from_config"]
```
