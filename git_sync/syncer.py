import os
import logging
from pathlib import Path

from git_sync import github, git_ops
from git_sync.config import GITHUB_USER

log = logging.getLogger("git-sync")


def sync(project_path: str, commit_msg: str = "", private: bool = False) -> dict:
    """Sync a local project to GitHub. Creates repo if it doesn't exist."""
    project_path = os.path.expanduser(project_path)
    if not os.path.isdir(project_path):
        return {"ok": False, "error": f"Directory not found: {project_path}"}

    repo_name = Path(project_path).name
    steps: list[str] = []

    # 1. Ensure git repo
    git_ops.ensure_init(project_path)
    git_ops.ensure_gitignore(project_path)
    steps.append("git_init")

    # 2. Check / create GitHub repo
    if github.repo_exists(repo_name):
        steps.append(f"repo_exists: {GITHUB_USER}/{repo_name}")
    else:
        github.create_repo(repo_name, private=private)
        steps.append(f"repo_created: {GITHUB_USER}/{repo_name}")

    # 3. Configure remote
    git_ops.ensure_remote(project_path, repo_name)
    steps.append("remote_configured")

    # 4. Commit
    msg = commit_msg or "auto-sync"
    if git_ops.commit_all(project_path, msg):
        steps.append(f"committed: {msg}")
    else:
        steps.append("nothing_to_commit")

    # 5. Push
    ok, out = git_ops.push(project_path)
    if ok:
        steps.append("pushed")
    else:
        steps.append(f"push_failed: {out}")
        return {"ok": False, "steps": steps, "error": out}

    return {"ok": True, "repo": github.repo_url(repo_name), "steps": steps}
