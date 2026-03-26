from .base import *


DEBUG = True

CORS_ALLOW_CREDENTIALS = True

# Allow the frontend origin for CSRF checks (needed for cross-origin XHR POSTs)
# Django requires full scheme-host entries in CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://www.searcherlist.com",
    "https://api.searcherlist.com",
])

CSRF_COOKIE_SAMESITE = 'lax'
