#!/usr/bin/env bash
# SkyOps one-shot VPS setup (Ubuntu 22.04/24.04, run as root).
# Usage:  bash setup.sh yourdomain.com
set -euo pipefail

DOMAIN="${1:?usage: bash setup.sh yourdomain.com}"
APP_DIR=/opt/skyops

apt-get update
apt-get install -y python3 python3-venv python3-pip git curl

# --- app ---
mkdir -p "$APP_DIR"
# copy the skyops/ folder to the server first, e.g.:
#   scp -r skyops root@SERVER:/opt/
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/backend/requirements.txt"

# --- systemd service (auto-start, auto-restart) ---
cat > /etc/systemd/system/skyops.service <<EOF
[Unit]
Description=SkyOps drone platform
After=network.target

[Service]
WorkingDirectory=$APP_DIR/backend
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now skyops

# --- Caddy: HTTPS reverse proxy with automatic certificates ---
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  > /etc/apt/sources.list.d/caddy-stable.list
apt-get update && apt-get install -y caddy

cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    reverse_proxy 127.0.0.1:8000
}
EOF
systemctl restart caddy

echo "Done. Point the domain's A record at this server's IP."
echo "SkyOps will be live at https://$DOMAIN"
