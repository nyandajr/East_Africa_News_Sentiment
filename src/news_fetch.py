"""News fetch module for East Africa News Sentiment.

Replaced NewsAPI's top-headlines country filter for east_africa (2026-07-08):
NewsAPI's free tier only documents 'us' as a supported country. ke/tz/ug/rw/bi
were never real -- verified this returned ~0.75% "east_africa"-labeled rows
over months, and even those were non-regional sources (The Punch, ABC News,
etc.), not ke/tz/ug/rw/bi outlets.

New approach, verified live per-source before switching:
  - Kenya: NewsData.io (confirmed real local source, e.g. The Standard,
    standardmedia.co.ke)
  - Tanzania/Uganda: Google News country editions (confirmed real local
    sources, e.g. thecitizen.co.tz, ippmedia.co.tz, ChimpReports, Nilepost)
  - Rwanda/Burundi: Google News search query -- Google has no dedicated local
    edition for these two, so search is a fallback. Weaker for Burundi
    specifically (mostly-French-language media market, thin English
    coverage) but still real regional/international content, not generic
    pan-African wire noise.

NewsData.io was tried for all five countries first; only Kenya returned
genuinely local results there -- tz/ug/rw/bi came back tagged with 20-45
countries simultaneously on the same wire articles (Menafn, IGN Africa),
i.e. generic pan-African syndication, not local news. Hence the split
approach instead of a single provider.
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

# DO NOT use load_dotenv() here — GitHub Actions injects secrets directly
# as environment variables. load_dotenv() would override them with an
# empty .env file and break the workflow.
# Local development: set NEWSAPI_KEY / NEWSDATA_API_KEY in your terminal.

NEWSAPI_KEY  = os.getenv('NEWSAPI_KEY')
NEWSDATA_KEY = os.getenv('NEWSDATA_API_KEY')

BASE_URL_TOP = 'https://newsapi.org/v2/top-headlines'
_GLOBAL_COUNTRIES = ['us', 'gb', 'au', 'ca', 'za']

GOOGLE_NEWS_COUNTRY_EDITIONS = {'tz': 'TZ', 'ug': 'UG'}
GOOGLE_NEWS_SEARCH_TERMS = {'rw': 'Rwanda', 'bi': 'Burundi'}


def _build_top_params(country: str, page=1):
    return {
        'country':  country,
        'language': 'en',
        'pageSize': 100,
        'page':     page,
        'apiKey':   NEWSAPI_KEY,
    }


def _fetch_global(now):
    if not NEWSAPI_KEY:
        print('[news_fetch] NEWSAPI_KEY not set, skipping global category')
        return []

    all_articles = []
    for cc in _GLOBAL_COUNTRIES:
        page = 1
        while True:
            try:
                resp = requests.get(BASE_URL_TOP, params=_build_top_params(cc, page), timeout=20)
            except Exception as e:
                print(f'[news_fetch] global fetch failed for {cc}: {e}')
                break

            if not resp.ok:
                break

            articles = resp.json().get('articles', [])
            if not articles:
                break

            for a in articles:
                all_articles.append({
                    'category':    'global',
                    'source_name': a.get('source', {}).get('name', ''),
                    'author':      a.get('author'),
                    'title':       a.get('title'),
                    'description': a.get('description'),
                    'url':         a.get('url'),
                    'publishedAt': a.get('publishedAt'),
                    'fetchedAt':   now,
                })

            if len(articles) < 100:
                break
            page += 1

    return all_articles


def _fetch_newsdata_kenya(now):
    if not NEWSDATA_KEY:
        print('[news_fetch] NEWSDATA_API_KEY not set, skipping Kenya')
        return []

    try:
        resp = requests.get(
            'https://newsdata.io/api/1/news',
            params={'apikey': NEWSDATA_KEY, 'country': 'ke', 'language': 'en'},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f'[news_fetch] NewsData.io fetch failed for Kenya: {e}')
        return []

    articles = []
    for a in data.get('results', []):
        articles.append({
            'category':    'east_africa',
            'source_name': a.get('source_name', ''),
            'author':      ', '.join(a.get('creator') or []) or None,
            'title':       a.get('title'),
            'description': a.get('description'),
            'url':         a.get('link'),
            'publishedAt': a.get('pubDate'),
            'fetchedAt':   now,
        })
    return articles


def _parse_google_news_rss(url, now):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f'[news_fetch] Google News RSS fetch failed for {url}: {e}')
        return []

    articles = []
    for item in root.findall('.//item'):
        title_el   = item.find('title')
        link_el    = item.find('link')
        pubdate_el = item.find('pubDate')
        source_el  = item.find('source')
        desc_el    = item.find('description')

        articles.append({
            'category':    'east_africa',
            'source_name': source_el.text if source_el is not None else '',
            'author':      None,
            'title':       title_el.text if title_el is not None else None,
            'description': desc_el.text if desc_el is not None else None,
            'url':         link_el.text if link_el is not None else None,
            'publishedAt': pubdate_el.text if pubdate_el is not None else None,
            'fetchedAt':   now,
        })
    return articles


def _fetch_east_africa(now):
    articles = _fetch_newsdata_kenya(now)

    for gl in GOOGLE_NEWS_COUNTRY_EDITIONS.values():
        url = f'https://news.google.com/rss?hl=en-{gl}&gl={gl}&ceid={gl}:en'
        articles.extend(_parse_google_news_rss(url, now))

    for query in GOOGLE_NEWS_SEARCH_TERMS.values():
        url = f'https://news.google.com/rss/search?q={query}&hl=en-KE&gl=KE&ceid=KE:en'
        articles.extend(_parse_google_news_rss(url, now))

    return articles


def fetch_headlines(category: str, hours_back=1):
    if category not in ['east_africa', 'global']:
        raise ValueError(f'Invalid category: {category}')

    now = datetime.now(timezone.utc).isoformat()

    if category == 'east_africa':
        return _fetch_east_africa(now)
    return _fetch_global(now)
