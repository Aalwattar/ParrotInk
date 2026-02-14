import tomllib
from pathlib import Path


def get_app_version() -> str:
    """
    Reads the application version from pyproject.toml.
    Returns "unknown" if the file or version key is not found.
    """
    # Try to find pyproject.toml in the project root
    # engine/ui_utils.py -> parent is engine -> parent is root
    root_path = Path(__file__).parent.parent
    pyproject_path = root_path / "pyproject.toml"

    if not pyproject_path.exists():
        return "unknown"

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "unknown")
            return str(version)
    except Exception:
        return "unknown"
