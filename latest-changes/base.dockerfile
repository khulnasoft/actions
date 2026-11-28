FROM python:3.14-slim@sha256:f57c4c23b985d95deea5bc5249e2f9c8a512b4cc9d5d3fd31900cbd2f5f0a604

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git=1:2.47.3-0+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY latest-changes/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY latest-changes/latest_changes ./latest_changes

ENV PYTHONPATH=/app

CMD ["python", "-m", "latest_changes"]