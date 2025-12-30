FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_music_bot ./telegram_music_bot

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "telegram_music_bot.bot_client"]
