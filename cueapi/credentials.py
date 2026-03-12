"""Credential storage and resolution for CueAPI CLI."""
from __future__ import annotations

import json
import os
import platform
import stat
from pathlib import Path
from typing import Any, Dict, Optional

import click


def _default_creds_path() -> Path:
    """Get the default credentials file path based on OS."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "cueapi" / "credentials.json"


CREDS_PATH = _default_creds_path()


def load_credentials(creds_file: Optional[Path] = None) -> Dict[str, Any]:
    """Load credentials from file. Returns empty dict if file doesn't exist."""
    path = creds_file or CREDS_PATH
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_credentials(
    creds_file: Optional[Path] = None,
    profile: str = "default",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Save credentials for a profile. Creates parent directories if needed."""
    path = creds_file or CREDS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    creds = load_credentials(path)
    if data:
        creds[profile] = data

    with open(path, "w") as f:
        json.dump(creds, f, indent=2)

    # Set file permissions to 600 (owner read/write only)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows may not support chmod


def remove_credentials(
    creds_file: Optional[Path] = None,
    profile: str = "default",
) -> Optional[str]:
    """Remove a profile from credentials. Returns email if found."""
    path = creds_file or CREDS_PATH
    creds = load_credentials(path)
    if profile not in creds:
        return None

    email = creds[profile].get("email", "unknown")
    del creds[profile]

    with open(path, "w") as f:
        json.dump(creds, f, indent=2)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    return email


def remove_all_credentials(creds_file: Optional[Path] = None) -> None:
    """Delete the entire credentials file."""
    path = creds_file or CREDS_PATH
    if path.exists():
        path.unlink()


def resolve_api_key(
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
    creds_file: Optional[Path] = None,
) -> str:
    """Resolve API key from env var, flag, or credentials file.

    Priority: CUEAPI_API_KEY env > --api-key flag > profile from file.
    """
    env_key = os.environ.get("CUEAPI_API_KEY")
    if env_key:
        return env_key

    if api_key:
        return api_key

    profile_name = profile or os.environ.get("CUEAPI_PROFILE", "default")
    creds = load_credentials(creds_file)
    if profile_name in creds:
        return creds[profile_name]["api_key"]

    raise click.ClickException(
        "Not logged in. Run `cueapi login` to authenticate."
    )


def resolve_api_base(
    profile: Optional[str] = None,
    creds_file: Optional[Path] = None,
) -> str:
    """Resolve API base URL from credentials or default."""
    env_base = os.environ.get("CUEAPI_API_BASE")
    if env_base:
        return env_base

    profile_name = profile or os.environ.get("CUEAPI_PROFILE", "default")
    creds = load_credentials(creds_file)
    if profile_name in creds:
        return creds[profile_name].get("api_base", "https://api.cueapi.ai/v1")

    return "https://api.cueapi.ai/v1"


def get_profile_info(
    profile: Optional[str] = None,
    creds_file: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Get full profile data. Returns None if not found."""
    profile_name = profile or os.environ.get("CUEAPI_PROFILE", "default")
    creds = load_credentials(creds_file)
    return creds.get(profile_name)
