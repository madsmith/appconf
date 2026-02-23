from typing import Any
from omegaconf import OmegaConf, DictConfig, ListConfig, MISSING

RawOmegaConfConfig = DictConfig | ListConfig


class OmegaConfig:
    def __init__(self, config: RawOmegaConfConfig):
        assert isinstance(config, (DictConfig, ListConfig)), (
            f"Config must be a DictConfig or ListConfig, got {type(config)}"
        )
        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        return OmegaConf.select(self._config, key, default=default)

    def __contains__(self, key: str) -> bool:
        """
        Support `'key' in config` using OmegaConf's select with a sentinel.
        Returns True if the key path exists in the config (even if its value is None).
        """
        return OmegaConf.select(self._config, key, default=MISSING) is not MISSING

    def set(self, key: str, value: Any) -> None:
        def highlight_key(parts, highlight_idx):
            return '.'.join([
                p if j != highlight_idx else f'**{p}**'
                for j, p in enumerate(parts)
            ])

        key_parts = key.split('.')

        current_config = self._config
        for i, part in enumerate(key_parts[:-1]):
            if isinstance(current_config, DictConfig):
                if part not in current_config:
                    current_config[part] = {}
                current_config = current_config[part]
            elif isinstance(current_config, ListConfig):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current_config):
                        highlighted = highlight_key(key_parts, i)
                        raise ValueError(f"Index {index} out of bounds in \"{highlighted}\"")
                    current_config = current_config[index]
                except ValueError:
                    highlighted = highlight_key(key_parts, i)
                    raise ValueError(f"Invalid list index: {part} in \"{highlighted}\"")
            else:
                highlighted = highlight_key(key_parts, i)
                raise ValueError(f"Config must be a DictConfig or ListConfig at \"{highlighted}\"")

        last_part = key_parts[-1]
        if isinstance(current_config, DictConfig):
            current_config[last_part] = value
        elif isinstance(current_config, ListConfig):
            try:
                index = int(last_part)
                if index < 0 or index >= len(current_config):
                    highlighted = highlight_key(key_parts, len(key_parts)-1)
                    raise ValueError(f"Index {index} out of bounds in \"{highlighted}\"")
                current_config[index] = value
            except ValueError:
                highlighted = highlight_key(key_parts, len(key_parts)-1)
                raise ValueError(f"Invalid list index: {last_part} in \"{highlighted}\"")
        else:
            highlighted = highlight_key(key_parts, len(key_parts)-1)
            raise ValueError(f"Config must be a DictConfig or ListConfig at \"{highlighted}\"")

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        self.set(name, value)

    def __str__(self) -> str:
        return str(self._config)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._config!r})"
