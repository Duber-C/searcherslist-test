from .base import *

DEBUG = False

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "https://www.searcherlist.com",
])
