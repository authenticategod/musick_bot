FROM python:3.10-slim

WORKDIR /app

ARG CACHE_BUST=1
ARG RAILWAY_GIT_COMMIT_SHA=unknown

# System deps (ffmpeg needed for audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN echo "Cache bust: ${CACHE_BUST} commit: ${RAILWAY_GIT_COMMIT_SHA}" \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --pre -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot_client.py"]
