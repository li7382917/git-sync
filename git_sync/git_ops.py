import logging
import subprocess
from pathlib import Path

from git_sync.config import GITHUB_USER, GITHUB_TOKEN

log = logging.getLogger("git-sync")


def run(cmd: list[str], cwd: str) -> tuple[int, str]:
    """Run a shell command, return (returncode, combined output)."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


def ensure_init(project_path: str):
    """Make sure the directory is a git repo."""
    if not (Path(project_path) / ".git").exists():
        run(["git", "init"], cwd=project_path)
        run(["git", "checkout", "-b", "main"], cwd=project_path)
        log.info("Initialized new git repo at %s", project_path)


def ensure_gitignore(project_path: str):
    """Create a basic .gitignore if none exists."""
    gi = Path(project_path) / ".gitignore"
    if not gi.exists():
        gi.write_text(
            "__pycache__/\n*.pyc\n.venv/\n.env\n.idea/\n*.egg-info/\n"
            "dist/\nbuild/\nnode_modules/\n"
        )


def ensure_remote(project_path: str, repo_name: str):
    """Set origin remote, update URL if already exists."""
    url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
    rc, _ = run(["git", "remote", "get-url", "origin"], cwd=project_path)
    if rc != 0:
        run(["git", "remote", "add", "origin", url], cwd=project_path)
    else:
        run(["git", "remote", "set-url", "origin", url], cwd=project_path)


def commit_all(project_path: str, message: str) -> bool:
    """Stage and commit. Returns True if a commit was made."""
    run(["git", "add", "-A"], cwd=project_path)
    rc, _ = run(["git", "diff", "--cached", "--quiet"], cwd=project_path)
    if rc != 0:
        run(["git", "commit", "-m", message], cwd=project_path)
        return True
    return False


def push(project_path: str) -> tuple[bool, str]:
    """Push to origin. Tries main, then master, then force-push main."""
    for args in (
        ["git", "push", "-u", "origin", "main"],
        ["git", "push", "-u", "origin", "master"],
        ["git", "push", "--force", "-u", "origin", "main"],
    ):
        rc, out = run(args, cwd=project_path)
        if rc == 0:
            return True, out
    return False, out
