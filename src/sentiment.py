"""Sentiment analysis helpers using VADER."""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def score_headlines(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    scores = df['title'].apply(lambda text: analyzer.polarity_scores(str(text)))
    score_df = pd.json_normalize(scores)

    df = df.reset_index(drop=True).copy()
    df = pd.concat([df, score_df], axis=1)

    def label(compound):
        if compound >= 0.05:
            return 'positive'
        if compound <= -0.05:
            return 'negative'
        return 'neutral'

    df['sentiment_label'] = df['compound'].apply(label)
    return df
