#!/bin/bash
set -e

source /app/deploy/.image

echo "==> Logging into ECR..."
REGION=$(aws configure get region || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "==> Pulling image $ECR_IMAGE..."
docker pull $ECR_IMAGE

echo "==> Running collectstatic..."
docker run --rm --env-file /app/.env.production -e DJANGO_SETTINGS_MODULE=config.settings.prod $ECR_IMAGE python manage.py collectstatic --noinput

echo "==> Running migrations..."
docker run --rm --env-file /app/.env.production -e DJANGO_SETTINGS_MODULE=config.settings.prod $ECR_IMAGE python manage.py migrate --noinput

echo "==> Fixing ownership..."
chown -R django:django /app
