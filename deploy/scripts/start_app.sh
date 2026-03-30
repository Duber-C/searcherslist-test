#!/bin/bash
set -e

echo "==> Restarting Gunicorn..."
systemctl daemon-reload
systemctl restart gunicorn

echo "==> Reloading Nginx..."
systemctl reload nginx
