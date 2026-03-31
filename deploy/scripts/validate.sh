#!/bin/bash
set -e

echo "==> Validating service is up..."
sleep 3

if ! docker compose -f /app/prod.yml ps django | grep -q "Up"; then
  echo "ERROR: django container is not running"
  exit 1
fi

# Check HTTP response from localhost
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/login/ || true)
if [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "301" ] && [ "$HTTP_STATUS" != "302" ]; then
  echo "WARNING: Unexpected HTTP status $HTTP_STATUS from /admin/login/"
fi

echo "==> Validation passed."
