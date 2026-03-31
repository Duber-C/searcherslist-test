#!/bin/bash
set -e

echo "==> Fixing ownership..."
chown -R django:django /app
