from __future__ import annotations
import os
from pathlib import Path

def hive_home() -> Path:
    """Return the configured HIVE data directory, creating it if necessary."""
    path = Path(os.environ.get("HIVE_HOME", Path.home() / ".hive")).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path

def database_path() -> Path:
    return hive_home() / "hive.db"

def log_path() -> Path:
    return hive_home() / "logs" / "hive.log"
