#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/knx-raspi-status-leds"
SERVICE_NAME="raspi-status-leds.service"

sudo mkdir -p "$APP_DIR"
sudo cp raspi_status_leds.py "$APP_DIR/"

if [ -f config.json ]; then
  sudo cp config.json "$APP_DIR/config.json"
elif [ ! -f "$APP_DIR/config.json" ]; then
  sudo cp config.example.json "$APP_DIR/config.json"
fi

sudo cp "$SERVICE_NAME" "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "Instalado. Ver estado con:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
