# Deploying SkyOps to a VPS

Requirements: any small Ubuntu VPS (1 vCPU / 1 GB RAM is enough for the
demo; 2 GB recommended if the AI video runs there) with root SSH, plus
a domain name.

Steps (10 minutes total):

1. Buy the VPS + domain. Point the domain's A record at the VPS IP.
2. Copy the project up:  `scp -r skyops root@SERVER_IP:/opt/`
3. SSH in and run:       `bash /opt/skyops/deploy/setup.sh yourdomain.com`
4. Open https://yourdomain.com - done. HTTPS certificate is automatic.

What the script sets up:
- Python venv with all requirements
- systemd service `skyops` (starts on boot, restarts on crash)
- Caddy reverse proxy with automatic Let's Encrypt HTTPS

Notes:
- The AI video needs ~1.5 GB RAM (YOLO). On a 1 GB box, either add
  swap (`fallocate -l 2G /swapfile; mkswap /swapfile; swapon /swapfile`)
  or accept the camera panel offline - the fleet demo still works.
- Copy `backend/tiles/` too - the map then never depends on OSM.
- Logs: `journalctl -u skyops -f`
- Update: copy new files, then `systemctl restart skyops`.

Checklist for judging whether a cheap hosting offer fits:
- MUST have: root SSH access (a "VPS", not "web hosting")
- MUST allow: running your own processes / Python
- Nice: 2 GB RAM, EU location (fast for the Polish audience)
