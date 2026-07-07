"""VM-side replacement for the GitHub Actions workflow -- run from the VM's
own crontab, not GitHub Actions (same migration already proven on the other
five repos in this account).
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_PATHS = ["data/sentiment_news.csv"]

load_dotenv(REPO_DIR / ".env")  # populates NEWSAPI_KEY, NEWSDATA_API_KEY, SMTP_* for run_update.py


def run(*args, check=True):
    return subprocess.run(list(args), cwd=str(REPO_DIR), check=check)


def sync_with_remote():
    # --hard, not --soft, and BEFORE run_update.py runs -- reset --soft only
    # moves HEAD, leaving stale index entries for files this script doesn't
    # explicitly `git add`, which then get silently recommitted on the next
    # force-push. Learned this the hard way on hormuz-strait-monitor.
    run("git", "fetch", "origin", "main")
    run("git", "reset", "--hard", "origin/main")


def git_commit_and_push():
    # freddynyanda@proton.me is Fred's real, verified GitHub email -- the
    # original workflow committed using secrets.COMMIT_USER/COMMIT_EMAIL,
    # whose actual verified status was never confirmed. Standardizing here.
    run("git", "config", "user.name", "nyandajr")
    run("git", "config", "user.email", "freddynyanda@proton.me")
    run("git", "add", *DATA_PATHS, check=False)

    diff = run("git", "diff", "--cached", "--quiet", check=False)
    if diff.returncode == 0:
        print("[run_and_push] no changes to commit")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    run("git", "commit", "-m", f"data: hourly sentiment update {timestamp}")
    run("git", "push", "--force", "origin", "HEAD:main")


def main():
    sync_with_remote()
    run(sys.executable, "src/run_update.py")
    git_commit_and_push()
    print("[run_and_push] done")


if __name__ == "__main__":
    main()
