"""Scheduler job for periodic news fetch and commit."""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import subprocess
import os

from .app import fetch_data


def run_job():
    ts = datetime.utcnow().isoformat()
    print(f'[{ts}] Running hourly fetch job')
    fetch_data('east_africa', 72)
    fetch_data('global', 72)

    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    subprocess.run(['git', 'add', 'data/sentiment_news.csv'], cwd=repo_dir)
    subprocess.run(['git', 'commit', '-m', f'data: hourly news sentiment update {ts}'], cwd=repo_dir)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, 'cron', minute=0)
    scheduler.start()
