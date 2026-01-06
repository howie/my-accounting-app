#!/usr/bin/env python3
"""Sync version from VERSION file to all project configuration files."""

import json
import re
import sys
from pathlib import Path


def read_version(project_root: Path) -> str:
    """Read version from VERSION file."""
    version_file = project_root / "VERSION"
    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found at {version_file}")
    return version_file.read_text().strip()


def update_pyproject_toml(file_path: Path, version: str) -> bool:
    """Update version in pyproject.toml."""
    if not file_path.exists():
        return False
    content = file_path.read_text()
    new_content = re.sub(r'^version = "[^"]*"', f'version = "{version}"', content, flags=re.MULTILINE)
    if new_content != content:
        file_path.write_text(new_content)
        return True
    return False


def update_package_json(file_path: Path, version: str) -> bool:
    """Update version in package.json."""
    if not file_path.exists():
        return False
    with open(file_path) as f:
        data = json.load(f)
    if data.get("version") != version:
        data["version"] = version
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return True
    return False


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent.parent

    try:
        version = read_version(project_root)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Syncing version: {version}")

    updates = []

    # Update root pyproject.toml
    root_pyproject = project_root / "pyproject.toml"
    if update_pyproject_toml(root_pyproject, version):
        updates.append(str(root_pyproject))

    # Update backend pyproject.toml
    backend_pyproject = project_root / "backend" / "pyproject.toml"
    if update_pyproject_toml(backend_pyproject, version):
        updates.append(str(backend_pyproject))

    # Update frontend package.json
    frontend_package = project_root / "frontend" / "package.json"
    if update_package_json(frontend_package, version):
        updates.append(str(frontend_package))

    if updates:
        print("Updated files:")
        for f in updates:
            print(f"  - {f}")
    else:
        print("All files already up to date.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
