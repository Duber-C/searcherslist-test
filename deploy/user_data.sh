#!/bin/bash
set -e

##############################################################################
# Bootstrap script for Amazon Linux 2023 — Django + Docker Compose
# Called once at instance launch via EC2 user_data.
##############################################################################

# ---------- System packages ----------
dnf update -y
dnf install -y git ruby wget

# ---------- Docker ----------
dnf install -y docker
systemctl enable docker
systemctl start docker

# Docker Compose plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# ---------- Install CodeDeploy agent ----------
cd /tmp
wget https://aws-codedeploy-${aws_region}.s3.${aws_region}.amazonaws.com/latest/install
chmod +x ./install
./install auto

# ---------- App user ----------
useradd -m -s /bin/bash django || true
usermod -aG docker django

# ---------- App directory ----------
mkdir -p /app/src /app/staticfiles /app/media /app/compose
chown -R django:django /app

# ---------- Environment file (.env.production) ----------
cat > /app/.env.production <<EOF
SECRET_KEY=${django_secret}
DEBUG=False
ALLOWED_HOSTS=${allowed_hosts}
CORS_ALLOWED_ORIGINS=${cors_origins}
CSRF_TRUSTED_ORIGINS=https://${allowed_hosts}

POSTGRES_DB=${db_name}
POSTGRES_USER=${db_user}
POSTGRES_PASSWORD=${db_password}
POSTGRES_HOST=${db_host}
POSTGRES_PORT=${db_port}

AWS_STORAGE_BUCKET_NAME=${media_bucket}
AWS_S3_CUSTOM_DOMAIN=
AWS_S3_REGION_NAME=${aws_region}

STATICFILES_BUCKET=${static_bucket}

OPENAI_API_KEY=${openai_api_key}
EOF
chmod 600 /app/.env.production
chown django:django /app/.env.production
