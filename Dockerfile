# Dockerfile for East Africa News Sentiment
# Build: docker build -t ea-news-sentiment .
# Run: docker run -d --name ea-news-sentiment -p 8501:8501 ea-news-sentiment

FROM python:3.12-slim

WORKDIR /app

# system deps for streamlit and pandas etc
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# expose streamlit port
EXPOSE 8501

ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
