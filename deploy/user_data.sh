#!/bin/bash
set -e

##############################################################################
# Bootstrap script for Amazon Linux 2023 — Django + Docker Compose
# Called once at instance launch via EC2 user_data.
##############################################################################

# ---------- System packages ----------
dnf update -y
dnf install -y git ruby wget jq

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

# ---------- Fetch secrets from Secrets Manager ----------
aws secretsmanager get-secret-value \
  --secret-id "${secret_name}" \
  --region "${aws_region}" \
  --query SecretString \
  --output text \
  | jq -r 'to_entries[] | "\(.key)=\(.value)"' > /app/.env.production

chmod 600 /app/.env.production
chown django:django /app/.env.production
