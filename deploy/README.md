# Webhook Listener Server

A single webhook listener server with a FastAPI endpoint, used currently for the Google Health Connect integration. Listener server is defined in `monitordb.server.py` and the route is owned by its integration in `monitordb.integration.google_health_connect.route.py`. Caddy is used as a reverse proxy to serve this service on a personal domain for easy sync access anywhere.

## Setup

Fill in `monitordb_template.service` and run as a systemd daemon with the following:

```
cp deploy/monitordb.service.example deploy/monitordb.service
sudo cp deploy/monitordb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now monitordb
```

Check the status with:

```
systemctl status monitordb
curl 127.0.0.1:8000/biometric
```

## Caddy

With Caddy isntalled, fill in `Caddyfile.example` and run as a systemd service with the following:

```
cp deploy/Caddyfile.example deploy/Caddyfile
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```