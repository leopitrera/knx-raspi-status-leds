#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/knx-raspi-status-leds"
SERVICE_NAME="raspi-status-leds.service"
SERVICE_DIR="$HOME/.config/systemd/user"

mkdir -p "$SERVICE_DIR"

if [ ! -f "$APP_DIR/config.json" ]; then
  cp "$APP_DIR/config.example.json" "$APP_DIR/config.json"
fi

cp "$APP_DIR/raspi-status-leds.user.service" "$SERVICE_DIR/$SERVICE_NAME"
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "Instalado como servicio de usuario. Ver estado con:"
echo "  systemctl --user status $SERVICE_NAME"
echo "  journalctl --user -u $SERVICE_NAME -f"
