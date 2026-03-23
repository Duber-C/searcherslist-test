#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/django-api/app"

cd "${APP_DIR}"
docker compose -f deploy/docker-compose.aws.yml up -d --build
