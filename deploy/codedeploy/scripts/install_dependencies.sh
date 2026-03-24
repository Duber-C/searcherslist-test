#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="/opt/django-api"
APP_DIR="${DEPLOY_ROOT}/app"

mkdir -p "${APP_DIR}/src/staticfiles" "${APP_DIR}/src/media"
touch "${DEPLOY_ROOT}/deploy.env"

if ! command -v docker >/dev/null 2>&1; then
  dnf update -y
  dnf install -y docker
  systemctl enable docker
  systemctl start docker
fi

if ! docker compose version >/dev/null 2>&1; then
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

if ! command -v aws >/dev/null 2>&1; then
  dnf install -y awscli
fi
