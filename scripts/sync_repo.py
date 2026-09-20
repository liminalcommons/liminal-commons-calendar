#!/usr/bin/env python3
"""Sync events.json with a GitHub-backed calendar repository."""
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPO", "psygen/liminal-commons-calendar")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DATA_DIR = Path("/app/data")
EVENTS_FILE = Path("/app/events.json")
REPO_DIR = DATA_DIR / "calendar-repo"


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def ensure_repo():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TOKEN:
        print("GITHUB_TOKEN not set; skipping repo sync.")
        return None

    remote = f"https://{TOKEN}@github.com/{REPO}.git"

    if REPO_DIR.exists():
        run(["git", "pull"], cwd=REPO_DIR)
    else:
        run(["git", "clone", remote, str(REPO_DIR)])

    return REPO_DIR


def sync():
    repo = ensure_repo()
    if repo is None:
        return

    repo_events = repo / "events.json"
    local_exists = EVENTS_FILE.exists()
    repo_exists = repo_events.exists()

    if not local_exists and not repo_exists:
        EVENTS_FILE.write_text("{}", encoding="utf-8")
        repo_events.write_text("{}", encoding="utf-8")
    elif not local_exists:
        EVENTS_FILE.write_text(repo_events.read_text(encoding="utf-8"), encoding="utf-8")
    elif not repo_exists:
        repo_events.write_text(EVENTS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        local = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
        remote = json.loads(repo_events.read_text(encoding="utf-8"))
        merged = {**remote, **local}
        text = json.dumps(merged, indent=2, ensure_ascii=False)
        EVENTS_FILE.write_text(text, encoding="utf-8")
        repo_events.write_text(text, encoding="utf-8")

    # Commit and push if changed
    run(["git", "add", "events.json"], cwd=repo, check=False)
    status = run(["git", "status", "--porcelain"], cwd=repo)
    if status.stdout.strip():
        now = datetime.now(timezone.utc).isoformat()
        run(["git", "config", "user.email", "bot@liminalcommons.local"], cwd=repo)
        run(["git", "config", "user.name", "Erik Calendar Bot"], cwd=repo)
        run(["git", "commit", "-m", f"Sync events from bot at {now}"], cwd=repo)
        run(["git", "push"], cwd=repo)
        print("Pushed events.json to GitHub.")
    else:
        print("No changes to push.")


if __name__ == "__main__":
    try:
        sync()
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
