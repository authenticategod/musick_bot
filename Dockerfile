FROM python:3.11-slim

WORKDIR /app

ARG CACHE_BUST=1

COPY requirements.txt ./
RUN echo "Cache bust: ${CACHE_BUST}" \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot_client.py"]
