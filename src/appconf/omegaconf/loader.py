import re
from pathlib import Path

from omegaconf import DictConfig, OmegaConf
from omegaconf.errors import InterpolationKeyError

from .errors import PrivateConfigError
from .omega_config import OmegaConfig, RawOmegaConfConfig

_INTERPOLATION_KEY_RE = re.compile(r"Interpolation key '(.+?)' not found")


class OmegaConfigLoader:
    """Loads YAML config files with OmegaConf, merging companion _private.yaml files."""

    @staticmethod
    def _load_raw(config_file: Path | str) -> RawOmegaConfConfig:
        """Load and process a YAML config, returning the raw OmegaConf object.

        1. Loads the specified YAML file via OmegaConf
        2. Looks for a sibling file with '_private' suffix and merges it if found
        3. Resolves all OmegaConf interpolations
        4. Removes the top-level 'private' key if present
        """
        if isinstance(config_file, str):
            config_file = Path(config_file)

        config = OmegaConf.load(config_file)

        # Look for companion _private.yaml file
        private_file = config_file.with_name(config_file.stem + "_private.yaml")
        if private_file.exists():
            config_private = OmegaConf.load(private_file)
            config = OmegaConf.merge(config, config_private)

        # Resolve all interpolations
        try:
            OmegaConf.resolve(config)
        except InterpolationKeyError as exc:
            match = _INTERPOLATION_KEY_RE.search(str(exc))
            key = match.group(1) if match else None
            if key and key.startswith("private."):
                raise PrivateConfigError(
                    key, config_file, private_file
                ) from exc
            raise

        # Strip private section if present
        if isinstance(config, DictConfig) and "private" in config:
            del config["private"]

        return config

    @staticmethod
    def load(config_file: Path | str) -> OmegaConfig:
        """Load a YAML config file and wrap it in an OmegaConfig."""
        return OmegaConfig(OmegaConfigLoader._load_raw(config_file))

    @staticmethod
    def load_raw(config_file: Path | str) -> RawOmegaConfConfig:
        """Load a YAML config file and return the raw DictConfig/ListConfig."""
        return OmegaConfigLoader._load_raw(config_file)
