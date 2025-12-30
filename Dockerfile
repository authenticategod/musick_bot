FROM python:3.10-slim

WORKDIR /app

ARG CACHE_BUST=1
ARG RAILWAY_GIT_COMMIT_SHA=unknown

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install base deps first
RUN echo "Cache bust: ${CACHE_BUST} commit: ${RAILWAY_GIT_COMMIT_SHA}" \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Install voice stack:
# - tgcalls dev6 exists for your environment
# - pytgcalls dev6 wrongly pins dev2, so install it with --no-deps
RUN python -m pip install --no-cache-dir --pre tgcalls==3.0.0.dev6 \
    && python -m pip install --no-cache-dir --pre --no-deps pytgcalls==3.0.0.dev6

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot_client.py"]
