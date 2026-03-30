#!/bin/bash
set -e

echo "==> Validating service is up..."
sleep 3

# Check gunicorn socket exists
if [ ! -S /run/gunicorn.sock ]; then
  echo "ERROR: gunicorn socket not found"
  exit 1
fi

# Check nginx is running
if ! systemctl is-active --quiet nginx; then
  echo "ERROR: nginx is not running"
  exit 1
fi

# Check HTTP response from localhost
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/login/ || true)
if [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "301" ] && [ "$HTTP_STATUS" != "302" ]; then
  echo "WARNING: Unexpected HTTP status $HTTP_STATUS from /admin/login/"
fi

echo "==> Validation passed."
