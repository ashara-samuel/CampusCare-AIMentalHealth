FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

# Run as a non-root user (hardening)
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# Hosts (Render/Fly/Railway) inject $PORT; fall back to 8000 locally.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import os,urllib.request,sys; p=os.getenv('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{p}/healthz').status==200 else 1)"

# Shell form so ${PORT} expands at runtime.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
