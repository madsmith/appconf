from pathlib import Path

from omegaconf import OmegaConf

from .omega_config import OmegaConfig, RawOmegaConfConfig


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
        OmegaConf.resolve(config)

        # Strip private section if present
        if "private" in config:
            del config["private"]  # type: ignore

        return config

    @staticmethod
    def load(config_file: Path | str) -> OmegaConfig:
        """Load a YAML config file and wrap it in an OmegaConfig."""
        return OmegaConfig(OmegaConfigLoader._load_raw(config_file))

    @staticmethod
    def load_raw(config_file: Path | str) -> RawOmegaConfConfig:
        """Load a YAML config file and return the raw DictConfig/ListConfig."""
        return OmegaConfigLoader._load_raw(config_file)
