"""FastAPI server for East Africa News Sentiment API."""

from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd

from .news_fetch import fetch_headlines
from .sentiment import score_headlines
from .storage import load_data, append_data

app = FastAPI(title='East Africa News Sentiment API')


@app.post('/fetch')
def fetch_data(category: str = 'east_africa', hours_back: int = 72):
    records = fetch_headlines(category, hours_back=hours_back)
    if not records:
        return {'status': 'no_data'}

    df = pd.DataFrame(records)
    scored = score_headlines(df)
    append_data(scored)

    return {'status': 'ok', 'new_count': len(scored)}


@app.get('/sentiment')
def get_sentiment(
    category: str = Query('east_africa', regex='^(east_africa|global)$'),
    since_hours: int = 24,
    min_compound: float = -1.0,
    max_compound: float = 1.0,
):
    df = load_data()
    if df.empty:
        return {'total': 0, 'records': []}

    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    df['publishedAt'] = pd.to_datetime(df['publishedAt'], errors='coerce')
    filtered = df[
        (df['category'] == category) &
        (df['publishedAt'] >= cutoff) &
        (df['compound'] >= min_compound) &
        (df['compound'] <= max_compound)
    ]

    return {'total': len(filtered), 'records': filtered.to_dict(orient='records')}


@app.get('/health')
def health():
    df = load_data()
    if df.empty:
        return {'status': 'ok', 'entries': 0, 'latest_fetched_at': None}

    latest = df['fetchedAt'].max() if 'fetchedAt' in df.columns else None
    if pd.notna(latest):
        latest = pd.to_datetime(latest).isoformat()

    return {
        'status': 'ok',
        'entries': len(df),
        'latest_fetched_at': latest,
        'source': 'sentiment_news.csv'
    }


@app.get('/summary')
def summary():
    df = load_data()
    if df.empty:
        return {'entries': 0}

    df['publishedAt'] = pd.to_datetime(df['publishedAt'], errors='coerce')
    cutoff = datetime.utcnow() - timedelta(hours=24)
    last24 = df[df['publishedAt'] >= cutoff]

    if last24.empty:
        return {'entries': 0}

    grouped = last24.groupby('category').agg(
        total=('title', 'count'),
        positive=('sentiment_label', lambda s: (s == 'positive').sum()),
        neutral=('sentiment_label', lambda s: (s == 'neutral').sum()),
        negative=('sentiment_label', lambda s: (s == 'negative').sum()),
        avg_compound=('compound', 'mean'),
    ).reset_index()

    return {'entries': len(last24), 'grouped': grouped.to_dict(orient='records')}
