import logging
import requests

from git_sync.config import GITHUB_API, GITHUB_USER, GITHUB_TOKEN

log = logging.getLogger("git-sync")


def headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def repo_exists(repo_name: str) -> bool:
    """Check if a repo exists under the user's GitHub account."""
    resp = requests.get(f"{GITHUB_API}/repos/{GITHUB_USER}/{repo_name}", headers=headers())
    return resp.status_code == 200


def create_repo(repo_name: str, private: bool = False) -> dict:
    """Create a new GitHub repo."""
    resp = requests.post(
        f"{GITHUB_API}/user/repos",
        headers=headers(),
        json={"name": repo_name, "private": private, "auto_init": False},
    )
    resp.raise_for_status()
    return resp.json()


def repo_url(repo_name: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{repo_name}"
