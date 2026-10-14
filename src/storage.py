"""CSV storage helper for sentiment records.

Used to reload and rewrite the ENTIRE sentiment_news.csv on every hourly
run -- both an expensive full-file read on a 956MB-RAM VM every cycle,
and (far more seriously) let the file grow completely unbounded for
~7 months until it hit GitHub's 100MB hard file-size limit on
2026-10-14, breaking every push from that point on. Now appends new
rows directly instead of reloading everything, and archives anything
older than ARCHIVE_AFTER_DAYS into a separate, one-time, gzip-compressed
file whenever the active file crosses MAX_ACTIVE_SIZE_BYTES -- so the
file committed every hour stays small indefinitely and this can't
recur, while historical data is kept (just moved out of the hot path,
never deleted).
"""

import gzip
import os

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CSV_FILE = os.path.join(DATA_DIR, 'sentiment_news.csv')
ARCHIVE_DIR = os.path.join(DATA_DIR, 'archive')

# How far back to check for duplicate articles -- a title/source/date
# match against a 7-month-old row isn't a real duplicate, so dedup only
# needs the recent window, not the full history.
DEDUP_WINDOW_DAYS = 7

# Once the active file crosses this, everything older than
# ARCHIVE_AFTER_DAYS gets split into data/archive/ and removed from the
# active file. 50MB leaves a lot of headroom under GitHub's 100MB limit.
MAX_ACTIVE_SIZE_BYTES = 50 * 1024 * 1024
ARCHIVE_AFTER_DAYS = 30

os.makedirs(DATA_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE, parse_dates=['publishedAt', 'fetchedAt'])
    return pd.DataFrame()


def _recent_dedup_keys(days=DEDUP_WINDOW_DAYS):
    if not os.path.exists(CSV_FILE):
        return set()
    existing = pd.read_csv(CSV_FILE, usecols=['category', 'source_name', 'title', 'publishedAt'])
    if existing.empty:
        return set()
    published = pd.to_datetime(existing['publishedAt'], utc=True, errors='coerce', format='mixed')
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
    recent = existing[published >= cutoff]
    return set(map(tuple, recent[['category', 'source_name', 'title', 'publishedAt']].astype(str).values))


def append_data(df: pd.DataFrame):
    if df.empty:
        return

    df = df.copy()
    seen = _recent_dedup_keys()
    if seen:
        keys = list(zip(
            df['category'].astype(str), df['source_name'].astype(str),
            df['title'].astype(str), df['publishedAt'].astype(str),
        ))
        df = df[[k not in seen for k in keys]]
    if df.empty:
        return

    write_header = not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0
    df.to_csv(CSV_FILE, mode='a', index=False, header=write_header)

    _archive_if_needed()


def _archive_if_needed():
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) < MAX_ACTIVE_SIZE_BYTES:
        return

    # fetchedAt mixes naive and timezone-aware timestamps across the
    # file's history. format='mixed' is required, not optional: without
    # it, pandas infers ONE format from the first row and silently
    # coerces every row that doesn't match it to NaT -- confirmed this
    # dropped 94,289 of 94,428 rows (99.85%) on this exact file during
    # testing, which then both "archived" and "kept active" would have
    # lost almost everything, since NaT rows match neither < nor >=
    # the cutoff. Caught before anything was committed or pushed.
    full = pd.read_csv(CSV_FILE)
    fetched = pd.to_datetime(full['fetchedAt'], utc=True, errors='coerce', format='mixed')
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=ARCHIVE_AFTER_DAYS)
    old, recent = full[fetched < cutoff], full[fetched >= cutoff]
    if old.empty:
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    start, end = fetched[old.index].min().date(), fetched[old.index].max().date()
    archive_path = os.path.join(ARCHIVE_DIR, f'sentiment_news_{start}_to_{end}.csv.gz')
    with gzip.open(archive_path, 'wt', newline='') as f:
        old.to_csv(f, index=False)

    recent.to_csv(CSV_FILE, index=False)
    print(f'[storage] archived {len(old)} rows -> {archive_path} '
          f'({os.path.getsize(archive_path) / 1e6:.1f} MB); active file now {len(recent)} rows')
