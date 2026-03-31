#!/bin/bash
set -e

echo "==> Starting application with Docker Compose..."
cd /app
docker compose -f prod.yml up -d --build
