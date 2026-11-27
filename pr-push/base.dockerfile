FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pr_push/ ./pr_push/
COPY version.txt .

ENV PYTHONPATH=/app

CMD ["python", "-m", "pr_push.action"]