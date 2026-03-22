"""News fetch module for East Africa News Sentiment API."""

import os
import requests
from datetime import datetime

# DO NOT use load_dotenv() here — GitHub Actions injects secrets directly
# as environment variables. load_dotenv() would override them with an
# empty .env file and break the workflow.
# Local development: set NEWSAPI_KEY in your terminal before running.

NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
if not NEWSAPI_KEY:
    raise RuntimeError('NEWSAPI_KEY is required in environment')

BASE_URL_TOP = 'https://newsapi.org/v2/top-headlines'

# Free tier only supports top-headlines endpoint
# everything endpoint requires paid plan
_EA_COUNTRIES     = ['ke', 'tz', 'ug', 'rw', 'bi']
_GLOBAL_COUNTRIES = ['us', 'gb', 'au', 'ca', 'za']


def _build_top_params(country: str, page=1):
    return {
        'country':  country,
        'language': 'en',
        'pageSize': 100,
        'page':     page,
        'apiKey':   NEWSAPI_KEY,
    }


def fetch_headlines(category: str, hours_back=1):
    if category not in ['east_africa', 'global']:
        raise ValueError(f'Invalid category: {category}')

    now          = datetime.utcnow()
    all_articles = []

    countries = _EA_COUNTRIES if category == 'east_africa' else _GLOBAL_COUNTRIES

    for cc in countries:
        page = 1
        while True:
            params = _build_top_params(cc, page)
            resp   = requests.get(BASE_URL_TOP, params=params, timeout=20)

            # Skip countries that return errors instead of crashing
            if not resp.ok:
                break

            payload  = resp.json()
            articles = payload.get('articles', [])

            if not articles:
                break

            for a in articles:
                all_articles.append({
                    'category':    category,
                    'source_name': a.get('source', {}).get('name', ''),
                    'author':      a.get('author'),
                    'title':       a.get('title'),
                    'description': a.get('description'),
                    'url':         a.get('url'),
                    'publishedAt': a.get('publishedAt'),
                    'fetchedAt':   now.isoformat(),
                })

            if len(articles) < 100:
                break
            page += 1

    return all_articles
