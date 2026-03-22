# East Africa News Sentiment API

Hourly job:
- fetch East Africa + Global headlines from NewsAPI
- run VADER sentiment analysis
- save to data/sentiment_news.csv
- auto-commit/push to GitHub

Run:
1. copy .env.example to .env and set keys
2. pip install -r requirements.txt
3. uvicorn src.app:app --reload --port 8000
4. in another shell: python src/scheduler.py

Endpoints:
- POST /fetch?category=east_africa&hours_back=1
- GET /sentiment?category=east_africa&since_hours=24
- GET /summary

## Reliability and uptime

1. Keep Streamlit and FastAPI active
   - FastAPI: `uvicorn src.app:app --host 127.0.0.1 --port 8000`
   - Streamlit Dashboard: `streamlit run src/streamlit_app.py --server.port 8501`
   - Use `tmux`, `screen`, or a systemd service to auto-restart on reboot.

2. Scheduler for hourly updates
   - `python -m src.scheduler` runs a cron-like job at minute 0 each hour.
   - Fetches `east_africa` and `global` (72h window) and appends to `data/sentiment_news.csv`.
   - Adds git commit and push in every run.

3. Auto-commit and push strategy
   - Scheduler executes:
     - `git add data/sentiment_news.csv`
     - `git commit -m "data: hourly news sentiment update <timestamp>"`
     - `git push origin main`
   - Ensure proper Git remote/auth setup with Personal Access Token.

4. Email alerts (optional)
   - Set up `msmtp` in `~/.msmtprc` or use Gmail app password.
   - Notification sent from scheduler step after each successful fetch/push.
   - Alerts include success/failure and summary counts.

## Health checks

- Verify streamlit: `curl -I http://127.0.0.1:8501`
- Verify API docs: `curl -I http://127.0.0.1:8000/docs`
- Verify data file: `tail data/sentiment_news.csv`
- Verify last refresh in dashboard (visible on top)
- Health endpoint: `curl http://127.0.0.1:8000/health` returns JSON with `status`, `entries`, and `latest_fetched_at`

## Production deployment (minimal downtime)

### Docker + Docker Compose

1. Build and run:
   - `docker compose up -d --build`
2. Containers:
   - `ea-news-sentiment` (Streamlit app)
   - `scheduler` (hourly data fetch + git commit/push)
3. Restart policy:
   - `restart: always` ensures crash recovery and automatic restart.
4. Environment:
   - `NEWSAPI_KEY` in `.env` or host environment.

### systemd service for Linux VM (backup)

Create file `/etc/systemd/system/ea-news-sentiment.service`:

```ini
[Unit]
Description=East Africa News Sentiment Streamlit service
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/repo
ExecStart=/path/to/.venv/bin/streamlit run src/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5
Environment="NEWSAPI_KEY=your_key_here"

[Install]
WantedBy=multi-user.target
```

Enable + start:
- `sudo systemctl daemon-reload`
- `sudo systemctl enable ea-news-sentiment`
- `sudo systemctl start ea-news-sentiment`

### Keepalive and monitoring

- Use external monitor (UptimeRobot, HetrixTools) pinging `http://yourhost:8501` every 5 min.
- Add a small health-check endpoint on FastAPI (e.g., `/health`) and use it.
- For extra robustness, run API and scheduler as separate services.

