FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY label_approved/ ./label_approved/

ENV PYTHONPATH=/app

CMD ["python", "-m", "label_approved"]
