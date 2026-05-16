import os
from pathlib import Path

from dotenv import load_dotenv

# Load project .env first
load_dotenv()

# If GITHUB_TOKEN is still empty, try ~/.hermes/.env
if not os.environ.get("GITHUB_TOKEN"):
    _hermes_env = Path.home() / ".hermes" / ".env"
    if _hermes_env.exists():
        load_dotenv(_hermes_env, override=True)

GITHUB_USER = os.environ.get("GITHUB_USER", "li7382917")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5050"))
