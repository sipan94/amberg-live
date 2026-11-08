# Optional alternative to the systemd setup. Put a reverse proxy with HTTPS in front
# (e.g. nginx from deploy/nginx.conf, or Caddy). Data lives in the /app/instance volume.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 amberg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt "psycopg[binary]~=3.2"

# CSS and vendor files are committed pre-built, so no Node is needed here.
COPY --chown=amberg:amberg . .
RUN mkdir -p instance/uploads instance/logs && chown -R amberg:amberg instance

USER amberg
EXPOSE 8000
VOLUME ["/app/instance"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

# Apply migrations and default categories on start, then serve.
CMD ["sh", "-c", "flask --app wsgi:app db upgrade && flask --app wsgi:app seed-categories && exec gunicorn -c deploy/gunicorn.conf.py --bind 0.0.0.0:8000 wsgi:app"]
