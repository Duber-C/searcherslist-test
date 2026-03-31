#!/bin/bash
set -e

source /app/deploy/.image
source /app/.deploy-config

echo "==> Refreshing secrets from Secrets Manager (env: $ENVIRONMENT)..."
aws secretsmanager get-secret-value \
  --secret-id "$SECRET_NAME" \
  --region "$AWS_REGION" \
  --query SecretString \
  --output text \
  | jq -r 'to_entries[] | "\(.key)=\(.value)"' > /app/.env.production
chmod 600 /app/.env.production

echo "==> Logging into ECR..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "==> Pulling image $ECR_IMAGE..."
docker pull "$ECR_IMAGE"

echo "==> Running collectstatic..."
docker run --rm --env-file /app/.env.production "$ECR_IMAGE" python manage.py collectstatic --noinput

echo "==> Running migrations..."
docker run --rm --env-file /app/.env.production "$ECR_IMAGE" python manage.py migrate --noinput

echo "==> Fixing ownership..."
chown -R django:django /app
