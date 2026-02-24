from pathlib import Path


class PrivateConfigError(Exception):
    """Raised when a config references a private interpolation key that is not defined."""

    def __init__(self, key: str, config_file: Path, private_file: Path) -> None:
        self.key = key
        self.config_file = config_file
        self.private_file = private_file
        verb = "is missing key" if private_file.exists() else "was not found"
        super().__init__(
            f"Config '{config_file.name}' references private key '{key}', "
            f"but '{private_file.name}' {verb}. "
            f"Create or update '{private_file}' with the required private keys."
        )
