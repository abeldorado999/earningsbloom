FROM python:3.12-slim

WORKDIR /app

# System deps for PyMuPDF and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev gcc libxml2-dev libxslt-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app (exclude venv, .env, __pycache__)
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV FLASK_ENV=production

EXPOSE 8080

# Gunicorn: 1 worker + 4 threads = handles concurrency, stays in Cloud Run free tier
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "app:app"]
