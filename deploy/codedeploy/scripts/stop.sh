#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/django-api/app"

if [ -f "${APP_DIR}/deploy/docker-compose.aws.yml" ]; then
  cd "${APP_DIR}"
  docker compose -f deploy/docker-compose.aws.yml down || true
fi
