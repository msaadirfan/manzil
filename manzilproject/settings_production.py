
from .settings import *   # import base settings
import os
import environ

# ---- env setup ----
env = environ.Env(DEBUG=(bool, False))
# read .env in BASE_DIR if present (useful locally). On Render you will set real env vars.
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ---- basic safety ----
DEBUG = env("DEBUG")  # default False from env definition above
SECRET_KEY = env("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[".onrender.com"])

# ---- CSRF / security headers ----
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://*.onrender.com"]
)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Respect proxy headers (Render sets X-Forwarded-Proto)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---- database (Render provides DATABASE_URL) ----
DATABASES = {
    "default": env.db("DATABASE_URL")
}

# ---- static files (WhiteNoise) ----
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ensure MIDDLEWARE is mutable and insert WhiteNoise after SecurityMiddleware if present
if isinstance(MIDDLEWARE, tuple):
    MIDDLEWARE = list(MIDDLEWARE)

whitenoise_mw = "whitenoise.middleware.WhiteNoiseMiddleware"
try:
    idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1
except ValueError:
    idx = 1
if whitenoise_mw not in MIDDLEWARE:
    MIDDLEWARE.insert(idx, whitenoise_mw)

# Use compressed hashed files for cache and smaller responses
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---- logging to console so Render captures logs ----
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": True},
    },
}
