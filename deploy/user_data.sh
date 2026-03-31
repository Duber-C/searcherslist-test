#!/bin/bash
set -e

##############################################################################
# Bootstrap script for Amazon Linux 2023 — Django + Gunicorn + Nginx
# Called once at instance launch via EC2 user_data.
##############################################################################

# ---------- System packages ----------
dnf update -y
dnf install -y python3.14 python3.14-pip python3.14-devel \
  nginx git postgresql16 ruby wget

# Install CodeDeploy agent
cd /tmp
wget https://aws-codedeploy-${aws_region}.s3.${aws_region}.amazonaws.com/latest/install
chmod +x ./install
./install auto

# ---------- App user ----------
useradd -m -s /bin/bash django || true

# ---------- App directory ----------
mkdir -p /app/src /app/staticfiles /app/media
chown -R django:django /app

# ---------- Virtual env ----------
python3.14 -m venv /app/venv
source /app/venv/bin/activate
pip install --upgrade pip gunicorn

# ---------- Environment file ----------
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

# ---------- Gunicorn systemd service ----------
cat > /etc/systemd/system/gunicorn.service <<EOF
[Unit]
Description=Gunicorn daemon for ${project_name}
After=network.target

[Service]
User=django
Group=django
WorkingDirectory=/app/src
EnvironmentFile=/app/.env.production
ExecStart=/app/venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/run/gunicorn.sock \
  --log-file /var/log/gunicorn.log \
  --access-logfile /var/log/gunicorn-access.log \
  config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ---------- Nginx config ----------
cat > /etc/nginx/conf.d/${project_name}.conf <<EOF
server {
    listen 80;
    server_name ${allowed_hosts};

    client_max_body_size 50M;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Remove default nginx site
rm -f /etc/nginx/conf.d/default.conf

# ---------- Enable services ----------
systemctl daemon-reload
systemctl enable nginx gunicorn
# Note: gunicorn won't start until app code is deployed via CodeDeploy
systemctl start nginx
