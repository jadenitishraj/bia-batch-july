#!/bin/bash
set -euo pipefail
dnf install -y python3.12 python3.12-pip nginx
useradd --system --home /opt/travel-demo travel-demo
mkdir -p /opt/travel-demo/backend
aws s3 cp s3://${code_bucket}/backend.tar.gz /tmp/backend.tar.gz --region ${region}
tar -xzf /tmp/backend.tar.gz -C /opt/travel-demo/backend
python3.12 -m venv /opt/travel-demo/venv
/opt/travel-demo/venv/bin/pip install -r /opt/travel-demo/backend/requirements.txt
cat > /opt/travel-demo/backend/.env <<'ENV'
AWS_REGION=${region}
CHAT_MODEL=us.amazon.nova-2-lite-v1:0
ENV
chown -R travel-demo:travel-demo /opt/travel-demo
cat > /etc/systemd/system/travel-demo.service <<'SERVICE'
[Unit]
Description=Travel Planner teaching backend
After=network-online.target
Wants=network-online.target
[Service]
User=travel-demo
WorkingDirectory=/opt/travel-demo/backend
ExecStart=/opt/travel-demo/venv/bin/python app.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
[Install]
WantedBy=multi-user.target
SERVICE
cat > /etc/nginx/conf.d/travel-demo.conf <<'NGINX'
server {
  listen 80;
  server_name _;
  client_max_body_size 100k;
  location /api/ {
    proxy_pass http://127.0.0.1:8003;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 120s;
  }
  location / { return 404; }
}
NGINX
cat > /etc/nginx/nginx.conf <<'NGINX'
user nginx;
worker_processes auto;
events { worker_connections 1024; }
http {
  include /etc/nginx/mime.types;
  include /etc/nginx/conf.d/*.conf;
}
NGINX
systemctl daemon-reload
systemctl enable --now travel-demo nginx
