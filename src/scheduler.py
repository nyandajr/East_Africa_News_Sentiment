"""Scheduler job for periodic news fetch, commit, push and email notification."""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import subprocess
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from .app import fetch_data

load_dotenv()


def send_email(subject: str, body: str) -> bool:
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')

    if not (smtp_user and smtp_pass and email_from and email_to):
        print('Email configuration missing; skipping email send.')
        return False

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, email_to.split(','), msg.as_string())
        print('Email sent successfully to', email_to)
        return True
    except Exception as e:
        print('Failed sending email:', e)
        return False


def run_job():
    ts = datetime.utcnow().isoformat()
    status = 'success'
    msg_lines = [f'### EA News Sentiment hourly update: {ts} UTC']

    try:
        msg_lines.append('Fetching East Africa and global headlines...')
        fetch_data('east_africa', 72)
        fetch_data('global', 72)

        repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        subprocess.run(['git', 'add', 'data/sentiment_news.csv'], cwd=repo_dir, check=False)
        subprocess.run(['git', 'commit', '-m', f'data: hourly news sentiment update {ts}'], cwd=repo_dir, check=False)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir, check=False)

        msg_lines.append('✅ Fetch, commit and push completed successfully.')

    except Exception as ex:
        status = 'failure'
        msg_lines.append(f'❌ Error during job: {ex}')

    body = '\n'.join(msg_lines)
    subject = f'EA News Sentiment update ({status}) {ts} UTC'
    send_email(subject, body)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, 'cron', minute=0)
    print('Scheduler started: run_job will execute at the top of every hour')
    scheduler.start()
