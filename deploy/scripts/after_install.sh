#!/bin/bash
set -e

echo "==> Installing/updating Python dependencies..."
source /app/venv/bin/activate
pip install --upgrade pip
pip install -r /app/requirements.txt

echo "==> Running database migrations..."
cd /app/src
DJANGO_SETTINGS_MODULE=config.settings.prod \
  python manage.py migrate --noinput

echo "==> Collecting static files..."
DJANGO_SETTINGS_MODULE=config.settings.prod \
  python manage.py collectstatic --noinput

echo "==> Fixing ownership..."
chown -R django:django /app
