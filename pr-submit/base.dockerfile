FROM python:3.14-slim@sha256:f57c4c23b985d95deea5bc5249e2f9c8a512b4cc9d5d3fd31900cbd2f5f0a604

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pr-submit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/python/actions_shared ./actions_shared
COPY pr-submit/pr_submit ./pr_submit
COPY pr-submit/version.txt .

ENV PYTHONPATH=/app

CMD ["python", "-m", "pr_submit.action"]