"""Enhanced Streamlit dashboard for East Africa News Sentiment."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import requests

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'sentiment_news.csv'

st.set_page_config(
    page_title='EA News Sentiment',
    layout='wide',
    initial_sidebar_state='expanded',
    page_icon='🌍'
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg:        #080e1a;
    --surface:   #0d1526;
    --border:    rgba(56,139,253,0.18);
    --accent:    #388bfd;
    --text:      #e6edf3;
    --muted:     #7d8590;
    --pos:       #3fb950;
    --neg:       #f85149;
    --neu:       #d29922;
    --glow:      0 0 24px rgba(56,139,253,0.25);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

div[data-baseweb="select"] > div {
    background: #111927 !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #1f6feb) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    box-shadow: var(--glow) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 32px rgba(56,139,253,0.45) !important;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: var(--glow); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.kpi-card.total::before { background: var(--accent); }
.kpi-card.pos::before   { background: var(--pos); }
.kpi-card.neu::before   { background: var(--neu); }
.kpi-card.neg::before   { background: var(--neg); }

.kpi-icon  { font-size: 24px; margin-bottom: 10px; display: block; }
.kpi-label { font-size: 11px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.kpi-value { font-size: 36px; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1; margin-bottom: 6px; }
.kpi-card.total .kpi-value { color: var(--accent); }
.kpi-card.pos   .kpi-value { color: var(--pos); }
.kpi-card.neu   .kpi-value { color: var(--neu); }
.kpi-card.neg   .kpi-value { color: var(--neg); }
.kpi-sub { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

.section-title {
    font-size: 13px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--muted);
    margin: 28px 0 14px;
    display: flex; align-items: center; gap: 8px;
}
.section-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.badge.pos { background: rgba(63,185,80,0.15);  color: var(--pos); border: 1px solid rgba(63,185,80,0.3); }
.badge.neg { background: rgba(248,81,73,0.15);  color: var(--neg); border: 1px solid rgba(248,81,73,0.3); }
.badge.neu { background: rgba(210,153,34,0.15); color: var(--neu); border: 1px solid rgba(210,153,34,0.3); }

.headline-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.headline-card:hover { border-color: var(--accent); }
.headline-title { font-size: 14px; font-weight: 500; color: var(--text); margin-bottom: 8px; line-height: 1.4; }
.headline-meta { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.score-bar-wrap { flex: 1; min-width: 80px; height: 4px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 4px; }

.sidebar-logo { text-align: center; padding: 20px 0 10px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
.sidebar-logo .logo-text { font-size: 20px; font-weight: 700; color: var(--accent); letter-spacing: -0.02em; }
.sidebar-logo .logo-sub  { font-size: 10px; color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; margin-top: 4px; }

.live-dot { display: inline-block; width: 8px; height: 8px; background: var(--pos); border-radius: 50%; margin-right: 6px; animation: pulse 1.8s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(1.3)} }

.country-chip { display: inline-flex; align-items: center; gap: 6px; background: rgba(56,139,253,0.1); border: 1px solid rgba(56,139,253,0.25); border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600; color: var(--accent); margin: 4px; }

[data-testid="stMetric"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; padding: 16px !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-family: 'JetBrains Mono', monospace !important; }
</style>
''', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    if not DATA_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(DATA_FILE, parse_dates=['publishedAt', 'fetchedAt'])


def badge_html(label):
    cls  = {'positive': 'pos', 'negative': 'neg', 'neutral': 'neu'}.get(label, 'neu')
    icon = {'positive': '▲',   'negative': '▼',   'neutral': '●'}.get(label, '●')
    return f'<span class="badge {cls}">{icon} {label}</span>'


def score_bar(compound):
    pct   = int((compound + 1) / 2 * 100)
    color = '#3fb950' if compound > 0.05 else '#f85149' if compound < -0.05 else '#d29922'
    return f'<div class="score-bar-wrap"><div class="score-bar-fill" style="width:{pct}%;background:{color};"></div></div>'


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('''
    <div class="sidebar-logo">
        <div class="logo-text">🌍 EA Pulse</div>
        <div class="logo-sub">News Sentiment Monitor</div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("**Category**")
    category = st.selectbox('', ['east_africa', 'global'],
        format_func=lambda x: '🌍 East Africa' if x == 'east_africa' else '🌐 Global',
        label_visibility='collapsed')

    st.markdown("**Time Window**")
    window = st.selectbox('', [1, 6, 12, 24, 48], index=3,
        format_func=lambda x: f'Last {x}h',
        label_visibility='collapsed')

    st.markdown("**Sentiment Filter**")
    sent_filter = st.multiselect('', ['positive', 'neutral', 'negative'],
        default=['positive', 'neutral', 'negative'],
        label_visibility='collapsed')

    st.markdown("---")
    st.markdown("**Manual Fetch**")
    if st.button('⚡ Fetch Latest Now'):
        try:
            resp = requests.post('http://127.0.0.1:8000/fetch?category=east_africa&hours_back=1', timeout=20)
            st.success(f'✅ {resp.status_code}')
        except Exception as e:
            st.error(f'❌ {e}')

    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#7d8590;text-align:center;"><span class="live-dot"></span>Auto-refreshes every 5 min</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
df = load_data()

st.markdown('''
<div style="margin-bottom:4px;">
    <span style="font-size:28px;font-weight:700;letter-spacing:-0.02em;color:#e6edf3;">
        East Africa <span style="color:#388bfd;">News Sentiment</span>
    </span>
</div>
<div style="font-size:13px;color:#7d8590;margin-bottom:8px;">
    <span class="live-dot"></span>Hourly sentiment analysis of trending headlines
</div>
''', unsafe_allow_html=True)

# Add last refresh indicator
if DATA_FILE.exists():
    last_refresh = pd.to_datetime(DATA_FILE.stat().st_mtime, unit='s', utc=True)
    last_refresh_utc = last_refresh.tz_convert('UTC')
    last_refresh_eat = last_refresh_utc.tz_convert('Etc/GMT-3')
    last_refresh = last_refresh_eat.strftime('%Y-%m-%d %H:%M:%S EAT')
    st.markdown(f'<div style="font-size:12px;color:#a3b8d1;margin-bottom:20px;">Last refreshed: <b>{last_refresh}</b></div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="font-size:12px;color:#a3b8d1;margin-bottom:20px;">Last refreshed: <b>N/A</b></div>', unsafe_allow_html=True)


if df.empty:
    st.markdown('''
    <div style="text-align:center;padding:60px 20px;background:#0d1526;border:1px solid rgba(56,139,253,0.18);border-radius:14px;">
        <div style="font-size:48px;margin-bottom:16px;">📡</div>
        <div style="font-size:18px;font-weight:600;color:#e6edf3;margin-bottom:8px;">No data yet</div>
        <div style="font-size:13px;color:#7d8590;">Run the scheduler or use the Fetch button to populate data.</div>
    </div>
    ''', unsafe_allow_html=True)
    st.stop()

# Apply filters
dff = df[df['sentiment_label'].isin(sent_filter) & (df['category'] == category)] if sent_filter else df[df['category'] == category]

# ── KPI Cards ──
total       = len(df)
pos         = (df['sentiment_label'] == 'positive').sum()
neu         = (df['sentiment_label'] == 'neutral').sum()
neg         = (df['sentiment_label'] == 'negative').sum()
pos_pct     = round(pos / total * 100, 1) if total else 0
neu_pct     = round(neu / total * 100, 1) if total else 0
neg_pct     = round(neg / total * 100, 1) if total else 0
avg_score   = round(df['compound'].mean(), 3) if 'compound' in df.columns else 0

st.markdown(f'''
<div class="kpi-grid">
    <div class="kpi-card total">
        <span class="kpi-icon">📰</span>
        <div class="kpi-label">Total Headlines</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-sub">avg score: {avg_score:+.3f}</div>
    </div>
    <div class="kpi-card pos">
        <span class="kpi-icon">📈</span>
        <div class="kpi-label">Positive</div>
        <div class="kpi-value">{pos:,}</div>
        <div class="kpi-sub">{pos_pct}% of total</div>
    </div>
    <div class="kpi-card neu">
        <span class="kpi-icon">➖</span>
        <div class="kpi-label">Neutral</div>
        <div class="kpi-value">{neu:,}</div>
        <div class="kpi-sub">{neu_pct}% of total</div>
    </div>
    <div class="kpi-card neg">
        <span class="kpi-icon">📉</span>
        <div class="kpi-label">Negative</div>
        <div class="kpi-value">{neg:,}</div>
        <div class="kpi-sub">{neg_pct}% of total</div>
    </div>
</div>
''', unsafe_allow_html=True)

# ── Trend Chart ──
st.markdown('<div class="section-title">📊 Sentiment Trend</div>', unsafe_allow_html=True)
chart_df = df.copy()
chart_df['publishedAt'] = pd.to_datetime(chart_df['publishedAt'], errors='coerce', utc=True)
cutoff   = pd.Timestamp.utcnow().tz_convert('UTC') - pd.Timedelta(hours=window)
chart_df = chart_df[(chart_df['category'] == category) & (chart_df['publishedAt'] >= cutoff)]

if not chart_df.empty and 'compound' in chart_df.columns:
    agg = chart_df.set_index('publishedAt').resample('1H')['compound'].mean().ffill()
    st.line_chart(agg, use_container_width=True, color='#388bfd')
else:
    st.info('No trend data for this window.')

# ── Headlines ──
st.markdown('<div class="section-title">🗞️ Latest Headlines</div>', unsafe_allow_html=True)
latest = dff.sort_values('publishedAt', ascending=False).head(20)

if latest.empty:
    st.info('No headlines match your filters.')
else:
    for _, row in latest.iterrows():
        label    = row.get('sentiment_label', 'neutral')
        compound = row.get('compound', 0)
        source   = row.get('source_name', 'Unknown')
        title    = row.get('title', 'No title')
        pub      = str(row.get('publishedAt', ''))[:16]
        color    = '#3fb950' if compound > 0.05 else '#f85149' if compound < -0.05 else '#d29922'

        st.markdown(f'''
        <div class="headline-card">
            <div class="headline-title">{title}</div>
            <div class="headline-meta">
                {badge_html(label)}
                <span>📡 {source}</span>
                <span>🕐 {pub}</span>
                <span>score: <b style="color:{color}">{compound:+.3f}</b></span>
                {score_bar(compound)}
            </div>
        </div>
        ''', unsafe_allow_html=True)

# ── Country Map ──
st.markdown('<div class="section-title">🗺️ Country Sentiment</div>', unsafe_allow_html=True)
coordinates = {
    'Kenya':    {'lat': -0.0236, 'lon': 37.9062},
    'Tanzania': {'lat': -6.3690, 'lon': 34.8888},
    'Uganda':   {'lat':  1.3733, 'lon': 32.2903},
    'Rwanda':   {'lat': -1.9403, 'lon': 29.8739},
    'Burundi':  {'lat': -3.3731, 'lon': 29.9189},
}
mini       = []
chips_html = ''
for country, cdata in coordinates.items():
    cset  = df[df['title'].str.contains(country, case=False, na=False)]
    score = round(cset['compound'].mean(), 3) if not cset.empty else 0.0
    count = len(cset)
    color = '#3fb950' if score > 0.05 else '#f85149' if score < -0.05 else '#d29922'
    chips_html += f'<span class="country-chip">{country} <b style="color:{color}">{score:+.3f}</b> ({count})</span>'
    mini.append({'latitude': cdata['lat'], 'longitude': cdata['lon'], 'avg_compound': score})

st.markdown(f'<div style="margin-bottom:14px;">{chips_html}</div>', unsafe_allow_html=True)
map_df = pd.DataFrame(mini)
if not map_df.empty:
    st.map(map_df[['latitude', 'longitude']], use_container_width=True)

# ── Hourly Delta ──
st.markdown('<div class="section-title">⚡ Hourly Delta</div>', unsafe_allow_html=True)
hourly = df.copy()
hourly['publishedAt'] = pd.to_datetime(hourly['publishedAt'], errors='coerce', utc=True)
cut    = pd.Timestamp.utcnow().tz_convert('UTC') - pd.Timedelta(hours=2)
hourly = hourly[hourly['publishedAt'] >= cut]
hg     = hourly.groupby([pd.Grouper(key='publishedAt', freq='1H'), 'category'])['compound'].mean().unstack('category')

if len(hg) >= 2:
    cols = st.columns(2)
    for i, cat in enumerate(['east_africa', 'global']):
        val = round((hg.iloc[-1].get(cat, 0) - hg.iloc[-2].get(cat, 0)) * 100, 2)
        with cols[i]:
            st.metric(f"{'🌍' if cat == 'east_africa' else '🌐'} {cat.replace('_',' ').title()}", f'{val:+.2f}%', delta=f'{val:+.2f}%')
else:
    st.info('Not enough data for delta.')

# ── Footer ──
st.markdown('''
<div style="margin-top:48px;padding-top:20px;border-top:1px solid rgba(56,139,253,0.18);display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:12px;color:#7d8590;">🌍 <b style="color:#388bfd;">EA Pulse</b> — East Africa News Sentiment</div>
    <div style="font-size:11px;color:#7d8590;font-family:'JetBrains Mono',monospace;">Built by Freddy Nyanda · nyandajr</div>
</div>
''', unsafe_allow_html=True)