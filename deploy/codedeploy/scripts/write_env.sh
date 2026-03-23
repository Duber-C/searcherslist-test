#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="/opt/django-api"
APP_DIR="${DEPLOY_ROOT}/app"

if [ -f "${DEPLOY_ROOT}/deploy.env" ]; then
  # shellcheck disable=SC1091
  source "${DEPLOY_ROOT}/deploy.env"
fi

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-searchers-backend-prod}"

aws ssm get-parameter \
  --name "/${PROJECT_NAME}/django/env" \
  --with-decryption \
  --region "${AWS_REGION}" \
  --query 'Parameter.Value' \
  --output text > "${APP_DIR}/.env.production"

aws ssm get-parameter \
  --name "/${PROJECT_NAME}/django/db" \
  --with-decryption \
  --region "${AWS_REGION}" \
  --query 'Parameter.Value' \
  --output text > "${APP_DIR}/.env.db"
