# appconf

Typed application config with YAML files and argparse override support, powered by [OmegaConf](https://github.com/omry/omegaconf).

Declare config properties as `Bind` descriptors on an `AppConfig` subclass.  Application can pass around a typed config file that resolves it's values to a sequence of providers such as argparse or a YAML backing.

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
from appconf import AppConfig, Bind

class ServerConfig(AppConfig):
    host = Bind[str]("server.host", default="0.0.0.0")
    port = Bind[int]("server.port", converter=int, default=3000)
    debug = Bind[bool]("server.debug")
```

And use it in your application:

```python
parser = argparse.ArgumentParser()
parser.add_argument("--host")
parser.add_argument("--port", type=int)
parser.add_argument("--debug", action="store_true", default=None)

args = parser.parse_args()
cfg = ServerConfig("config.yaml", args)

print(cfg.host)   # "localhost"  (from YAML)
print(cfg.port)   # 8080         (from YAML, converted to int)
print(cfg.debug)  # False        (from YAML)
```

When using defaults in argparse, these can shadow YAML resolution.  So it's recommended to call
`ArgParseWrapper.wrap()` on your parser to wrap defaults before parsing.  This lets
AppConfig distinguish explicit arguments from defaults during resolution.

```python
from appconf.providers.argparse import ArgParseWrapper

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default=8080)
parser.add_argument("--debug", action="store_true")

ArgParseWrapper.wrap(parser)
args = parser.parse_args()
cfg = ServerConfig("config.yaml", args)

print(cfg.host)   # "localhost"  (from YAML)
print(cfg.port)   # 8080         (from YAML, converted to int)
print(cfg.debug)  # False        (from YAML)
```
Command-line arguments take priority over the config file:

```
$ python app.py --port 9090
# cfg.port == 9090  (argparse wins)
```

## Resolution order

For each `Bind` property, values resolve in this order:

1. Explicit assignment (`cfg.port = 9090`)
2. argparse argument (if provided and not `None`)
3. YAML config file (via dot-path lookup)
4. `Bind` default

## Writing and saving

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
    save_dir = Bind[Path]("app.save_dir", converter=Path)
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
