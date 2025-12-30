FROM python:3.10-slim

WORKDIR /app

# Railway build args (safe to keep)
ARG CACHE_BUST=1
ARG RAILWAY_GIT_COMMIT_SHA=unknown

# System deps (ffmpeg is REQUIRED for music bots)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN echo "Cache bust: ${CACHE_BUST} commit: ${RAILWAY_GIT_COMMIT_SHA}" \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

ENV PYTHONUNBUFFERED=1

# Start bot
CMD ["python", "bot_client.py"]
