"""CSV storage helper for sentiment records."""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CSV_FILE = os.path.join(DATA_DIR, 'sentiment_news.csv')

os.makedirs(DATA_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE, parse_dates=['publishedAt', 'fetchedAt'])
    return pd.DataFrame()


def append_data(df: pd.DataFrame):
    existing = load_data()
    if existing.empty:
        merged = df
    else:
        merged = pd.concat([existing, df], ignore_index=True)

    merged.drop_duplicates(subset=['category', 'source_name', 'title', 'publishedAt'], inplace=True)
    merged.to_csv(CSV_FILE, index=False)
