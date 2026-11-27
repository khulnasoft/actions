FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pr_submit/ ./pr_submit/
COPY version.txt .

ENV PYTHONPATH=/app

CMD ["python", "-m", "pr_submit.action"]