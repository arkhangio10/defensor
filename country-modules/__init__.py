from pathlib import Path
import json
from typing import Any

_MODULES_DIR = Path(__file__).parent
_SUPPORTED = {"peru", "colombia", "mexico"}


def load_country_config(country: str) -> dict[str, Any]:
    """Load the config.json for a supported country. Falls back to peru."""
    key = country.lower()
    if key not in _SUPPORTED:
        key = "peru"
    path = _MODULES_DIR / key / "config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_countries() -> list[str]:
    return sorted(_SUPPORTED)
