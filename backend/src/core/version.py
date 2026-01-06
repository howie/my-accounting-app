"""Version information for the application."""

from functools import lru_cache
from pathlib import Path


@lru_cache
def get_version() -> str:
    """Get the application version from VERSION file."""
    # Try to find VERSION file relative to project root
    current = Path(__file__).resolve()
    for _ in range(5):  # Go up max 5 levels
        current = current.parent
        version_file = current / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()

    # Fallback version if file not found
    return "0.0.0"


VERSION = get_version()
