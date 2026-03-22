"""News fetch module for East Africa News Sentiment API."""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
if not NEWSAPI_KEY:
    raise RuntimeError('NEWSAPI_KEY is required in environment')

BASE_URL_EVERYTHING = 'https://newsapi.org/v2/everything'
BASE_URL_TOP = 'https://newsapi.org/v2/top-headlines'

_QUERIES = {
    'east_africa': 'Tanzania OR Kenya OR Uganda OR Rwanda OR Burundi',
    'global': 'world OR international',
}

_EA_COUNTRIES = ['ke','tz','ug','rw','bi']


def _build_everything_params(query: str, time_from: datetime, time_to: datetime, page=1):
    return {
        'q': query,
        'from': time_from.isoformat(timespec='seconds'),
        'to': time_to.isoformat(timespec='seconds'),
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 100,
        'page': page,
        'apiKey': NEWSAPI_KEY,
    }


def _build_top_params(country: str, page=1):
    return {
        'country': country,
        'language': 'en',
        'pageSize': 100,
        'page': page,
        'apiKey': NEWSAPI_KEY,
    }


def fetch_headlines(category: str, hours_back=24):
    if category not in _QUERIES:
        raise ValueError(f'Invalid category: {category}')

    now = datetime.utcnow()
    time_from = now - timedelta(hours=hours_back)
    time_to = now

    all_articles = []

    if category == 'east_africa':
        # Try top-headlines by country for better regional coverage
        for cc in _EA_COUNTRIES:
            page = 1
            while True:
                params = _build_top_params(cc, page)
                resp = requests.get(BASE_URL_TOP, params=params, timeout=20)
                resp.raise_for_status()
                payload = resp.json()
                articles = payload.get('articles', [])
                if not articles:
                    break
                for a in articles:
                    all_articles.append({
                        'category': category,
                        'source_name': a.get('source', {}).get('name', ''),
                        'author': a.get('author'),
                        'title': a.get('title'),
                        'description': a.get('description'),
                        'url': a.get('url'),
                        'publishedAt': a.get('publishedAt'),
                        'fetchedAt': now.isoformat(),
                    })
                if len(articles) < 100:
                    break
                page += 1

        # If still empty, fallback to everything query over 24h window
        if not all_articles:
            category_query = _QUERIES[category]
            page = 1
            while True:
                params = _build_everything_params(category_query, time_from, time_to, page)
                resp = requests.get(BASE_URL_EVERYTHING, params=params, timeout=20)
                resp.raise_for_status()
                payload = resp.json()
                articles = payload.get('articles', [])
                if not articles:
                    break
                for a in articles:
                    all_articles.append({
                        'category': category,
                        'source_name': a.get('source', {}).get('name', ''),
                        'author': a.get('author'),
                        'title': a.get('title'),
                        'description': a.get('description'),
                        'url': a.get('url'),
                        'publishedAt': a.get('publishedAt'),
                        'fetchedAt': now.isoformat(),
                    })
                if len(articles) < 100:
                    break
                page += 1

    else:
        # Global category uses everything query
        category_query = _QUERIES[category]
        page = 1
        while True:
            params = _build_everything_params(category_query, time_from, time_to, page)
            resp = requests.get(BASE_URL_EVERYTHING, params=params, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            articles = payload.get('articles', [])
            if not articles:
                break
            for a in articles:
                all_articles.append({
                    'category': category,
                    'source_name': a.get('source', {}).get('name', ''),
                    'author': a.get('author'),
                    'title': a.get('title'),
                    'description': a.get('description'),
                    'url': a.get('url'),
                    'publishedAt': a.get('publishedAt'),
                    'fetchedAt': now.isoformat(),
                })
            if len(articles) < 100:
                break
            page += 1

    return all_articles
