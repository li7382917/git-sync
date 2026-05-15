import os
import subprocess
import logging
from pathlib import Path

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("git-sync")

GITHUB_USER = os.environ.get("GITHUB_USER", "li7382917")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def _run(cmd: list[str], cwd: str) -> tuple[int, str]:
    """Run a shell command, return (returncode, combined output)."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out


def _repo_exists(repo_name: str) -> bool:
    """Check if a repo exists under the user's GitHub account."""
    resp = requests.get(f"{GITHUB_API}/repos/{GITHUB_USER}/{repo_name}", headers=_headers())
    return resp.status_code == 200


def _create_repo(repo_name: str, private: bool = False) -> dict:
    """Create a new GitHub repo."""
    resp = requests.post(
        f"{GITHUB_API}/user/repos",
        headers=_headers(),
        json={"name": repo_name, "private": private, "auto_init": False},
    )
    resp.raise_for_status()
    return resp.json()


def _ensure_git_init(project_path: str):
    """Make sure the directory is a git repo."""
    git_dir = Path(project_path) / ".git"
    if not git_dir.exists():
        _run(["git", "init"], cwd=project_path)
        _run(["git", "checkout", "-b", "main"], cwd=project_path)
        log.info("Initialized new git repo at %s", project_path)


def _ensure_remote(project_path: str, repo_name: str):
    """Set origin remote, update URL if already exists."""
    url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
    rc, out = _run(["git", "remote", "get-url", "origin"], cwd=project_path)
    if rc != 0:
        _run(["git", "remote", "add", "origin", url], cwd=project_path)
    else:
        _run(["git", "remote", "set-url", "origin", url], cwd=project_path)


def _ensure_gitignore(project_path: str):
    """Create a basic .gitignore if none exists."""
    gi = Path(project_path) / ".gitignore"
    if not gi.exists():
        gi.write_text(
            "__pycache__/\n*.pyc\n.venv/\n.env\n.idea/\n*.egg-info/\ndist/\nbuild/\nnode_modules/\n"
        )


def _sync(project_path: str, commit_msg: str = "", private: bool = False) -> dict:
    """Core sync logic: init → ensure remote → commit → push."""
    project_path = os.path.expanduser(project_path)
    if not os.path.isdir(project_path):
        return {"ok": False, "error": f"Directory not found: {project_path}"}

    repo_name = Path(project_path).name
    steps = []

    # 1. git init
    _ensure_git_init(project_path)
    _ensure_gitignore(project_path)
    steps.append("git_init")

    # 2. Check / create GitHub repo
    if _repo_exists(repo_name):
        steps.append(f"repo_exists: {GITHUB_USER}/{repo_name}")
    else:
        _create_repo(repo_name, private=private)
        steps.append(f"repo_created: {GITHUB_USER}/{repo_name}")

    # 3. Set remote
    _ensure_remote(project_path, repo_name)
    steps.append("remote_configured")

    # 4. Stage all changes
    _run(["git", "add", "-A"], cwd=project_path)

    # 5. Commit (skip if nothing to commit)
    msg = commit_msg or "auto-sync"
    rc, out = _run(["git", "diff", "--cached", "--quiet"], cwd=project_path)
    if rc != 0:
        _run(["git", "commit", "-m", msg], cwd=project_path)
        steps.append(f"committed: {msg}")
    else:
        steps.append("nothing_to_commit")

    # 6. Push (try main, then master)
    rc, out = _run(["git", "push", "-u", "origin", "main"], cwd=project_path)
    if rc != 0:
        rc, out = _run(["git", "push", "-u", "origin", "master"], cwd=project_path)
    if rc != 0:
        # First push to empty repo — force push
        rc, out = _run(["git", "push", "--force", "-u", "origin", "main"], cwd=project_path)

    if rc == 0:
        steps.append("pushed")
    else:
        steps.append(f"push_failed: {out}")
        return {"ok": False, "steps": steps, "error": out}

    repo_url = f"https://github.com/{GITHUB_USER}/{repo_name}"
    return {"ok": True, "repo": repo_url, "steps": steps}


# ── API Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "service": "git-sync",
        "endpoints": {
            "POST /sync": "Sync a local project to GitHub",
            "GET /check/<repo_name>": "Check if a repo exists",
        },
    })


@app.route("/sync", methods=["POST"])
def sync():
    """
    POST /sync
    Body: {"path": "/abs/path/to/project", "message": "optional commit msg", "private": false}
    """
    data = request.get_json(force=True)
    project_path = data.get("path", "")
    commit_msg = data.get("message", "")
    private = data.get("private", False)

    if not project_path:
        return jsonify({"ok": False, "error": "Missing 'path'"}), 400

    try:
        result = _sync(project_path, commit_msg, private)
        status = 200 if result["ok"] else 500
        return jsonify(result), status
    except Exception as e:
        log.exception("Sync failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/check/<repo_name>")
def check(repo_name: str):
    """GET /check/<repo_name> — Check if repo exists on GitHub."""
    exists = _repo_exists(repo_name)
    url = f"https://github.com/{GITHUB_USER}/{repo_name}" if exists else None
    return jsonify({"repo": repo_name, "exists": exists, "url": url})


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        # Try loading from hermes .env
        env_path = Path.home() / ".hermes" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    GITHUB_TOKEN = line.split("=", 1)[1].strip()
                    os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN
                    break
        if not GITHUB_TOKEN:
            log.error("GITHUB_TOKEN not set. Export it or add to ~/.hermes/.env")
            raise SystemExit(1)

    log.info("Starting git-sync on :5050  (user: %s)", GITHUB_USER)
    app.run(host="0.0.0.0", port=5050, debug=False)
