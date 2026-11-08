"""HTTP security headers and caching rules, applied to every response."""
from flask import request
from flask_login import current_user

# Only our own scripts run. Map tiles are the one external resource, and only after consent.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    # Inline style *attributes* are used for category colors chosen in the admin.
    # Inline <style> blocks / scripts are not used, so the risk is low.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://tile.openstreetmap.org",
    "font-src 'self'",
    "connect-src 'self'",
    "manifest-src 'self'",
    "worker-src 'self'",
    "frame-src 'none'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])

PERMISSIONS = "geolocation=(), camera=(), microphone=(), payment=(), usb=(), interest-cohort=()"
PRIVATE_BLUEPRINTS = {"auth", "dashboard", "admin"}


def register_security(app) -> None:
    @app.after_request
    def _headers(response):
        h = response.headers
        h.setdefault("Content-Security-Policy", CSP)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", PERMISSIONS)
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if app.config.get("SESSION_COOKIE_SECURE"):
            # Browsers then refuse plain http for this site for 2 years (only sent over https).
            h.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")

        # Pages for logged-in users must not end up in browser, proxy or service-worker caches.
        personal = request.blueprint in PRIVATE_BLUEPRINTS or (
            current_user.is_authenticated and response.mimetype == "text/html")
        if personal:
            h["Cache-Control"] = "private, no-store"
            if request.blueprint in PRIVATE_BLUEPRINTS:
                h["X-Robots-Tag"] = "noindex, nofollow"
        return response
