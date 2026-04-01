import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def load_config(config_path=None):
    """Load JSON config from the provided path or default config.json."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f), path


def resolve_path(config_file_path, configured_path):
    """Resolve a configured path relative to the config file location."""
    raw = Path(configured_path)
    if raw.is_absolute():
        return raw
    return (config_file_path.parent / raw).resolve()
