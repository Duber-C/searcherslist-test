#!/bin/bash
set -e

source /app/deploy/.image
export ECR_IMAGE

echo "==> Starting application with Docker Compose..."
cd /app
docker compose -f prod.yml up -d
