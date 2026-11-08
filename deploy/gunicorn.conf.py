"""gunicorn settings for the VPS (used by deploy/amberg-live.service)."""
import multiprocessing
import os

bind = "127.0.0.1:8000"  # only nginx talks to gunicorn

# One process with threads keeps the in-memory rate limiter consistent and is plenty
# for a city guide. With Redis as RATELIMIT_STORAGE_URI you can raise WORKERS.
workers = int(os.environ.get("WORKERS", 1))
threads = int(os.environ.get("THREADS", min(8, multiprocessing.cpu_count() * 2 + 1)))
worker_class = "gthread"

timeout = 30
graceful_timeout = 20
keepalive = 5
max_requests = 2000            # recycle workers now and then (guards against slow memory leaks)
max_requests_jitter = 200

accesslog = "-"                 # stdout -> journald
errorlog = "-"
loglevel = "info"
forwarded_allow_ips = "127.0.0.1"
