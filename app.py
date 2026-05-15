import logging

from flask import Flask, request, jsonify, render_template

from git_sync.config import GITHUB_TOKEN, GITHUB_USER
from git_sync.github import repo_exists, repo_url
from git_sync.syncer import sync

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("git-sync")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api")
def api_info():
    return jsonify({
        "service": "git-sync",
        "endpoints": {
            "POST /sync": "Sync a local project to GitHub",
            "GET /check/<repo_name>": "Check if a repo exists",
        },
    })


@app.route("/sync", methods=["POST"])
def sync_route():
    """POST /sync — Sync a local project to GitHub."""
    data = request.get_json(force=True)
    project_path = data.get("path", "")
    commit_msg = data.get("message", "")
    private = data.get("private", False)

    if not project_path:
        return jsonify({"ok": False, "error": "Missing 'path'"}), 400

    try:
        result = sync(project_path, commit_msg, private)
        status = 200 if result["ok"] else 500
        return jsonify(result), status
    except Exception as e:
        log.exception("Sync failed")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/check/<repo_name>")
def check(repo_name: str):
    """GET /check/<repo_name> — Check if repo exists on GitHub."""
    exists = repo_exists(repo_name)
    url = repo_url(repo_name) if exists else None
    return jsonify({"repo": repo_name, "exists": exists, "url": url})


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        log.error("GITHUB_TOKEN not set. Export it or add to ~/.hermes/.env")
        raise SystemExit(1)

    log.info("Starting git-sync on :5050  (user: %s)", GITHUB_USER)
    app.run(host="0.0.0.0", port=5050, debug=False)
