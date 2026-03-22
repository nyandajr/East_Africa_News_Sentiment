"""Simple entrypoint for GitHub Actions to run fetch -> sentiment -> storage."""

import os
from dotenv import load_dotenv
import pandas as pd

from news_fetch import fetch_headlines
from sentiment import score_headlines
from storage import append_data


def send_email(subject: str, body: str) -> bool:
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')

    if not (smtp_user and smtp_pass and email_from and email_to):
        print('Email configuration missing; skipping email send.')
        return False

    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

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
        print('Failed to send email:', e)
        return False


def main():
    load_dotenv('.env')

    fetched = []
    for category in ['east_africa', 'global']:
        fetched.extend(fetch_headlines(category, hours_back=72))

    if not fetched:
        body = 'No new articles fetched for East Africa and global.'
        print(body)
        send_email('EA News Sentiment update (no_data)', body)
        return

    df = pd.DataFrame(fetched)
    scored = score_headlines(df)
    append_data(scored)
    count = len(scored)
    body = f'Fetched and scored {count} records; appended to data/sentiment_news.csv.'
    print(body)
    send_email('EA News Sentiment update (success)', body)


if __name__ == '__main__':
    main()
