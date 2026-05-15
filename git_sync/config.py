import os
from pathlib import Path


def _load_token_from_env_file() -> str:
    """Try loading GITHUB_TOKEN from ~/.hermes/.env."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


GITHUB_USER = os.environ.get("GITHUB_USER", "li7382917")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "") or _load_token_from_env_file()
GITHUB_API = "https://api.github.com"

if GITHUB_TOKEN:
    os.environ.setdefault("GITHUB_TOKEN", GITHUB_TOKEN)
