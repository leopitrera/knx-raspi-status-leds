#!/usr/bin/env python3
"""Drive four Raspberry Pi GPIO LEDs with network, Connect, and KNX status."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "pins": {
        "raspberry": 5,
        "network": 6,
        "raspberry_connect": 13,
        "knx": 26,
    },
    "active_high": True,
    "check_interval_seconds": 5,
    "blink_interval_seconds": 0.5,
    "local_probe_host": "",
    "internet_probe_host": "8.8.8.8",
    "internet_probe_port": 53,
    "internet_timeout_seconds": 1.5,
    "dns_probe_name": "raspberrypi.com",
    "raspberry_connect_command": ["rpi-connect", "status"],
    "raspberry_connect_timeout_seconds": 3,
    "raspberry_connect_forbidden_words": [
        "not signed in",
        "signed out",
        "not running",
        "not installed",
        "not connected",
    ],
    "knx_check_mode": "off",
    "knx_host": "",
    "knx_port": 3671,
    "knx_timeout_seconds": 2,
}


@dataclass
class Status:
    raspberry: bool = True
    local_network: bool = False
    internet: bool = False
    dns: bool = False
    raspberry_connect: bool = False
    knx: bool = False


class MockLed:
    def __init__(self, name: str, pin: int) -> None:
        self.name = name
        self.pin = pin
        self.state: bool | None = None

    def set(self, value: bool) -> None:
        if self.state != value:
            logging.info("LED %-18s GPIO%-2s -> %s", self.name, self.pin, "ON" if value else "OFF")
            self.state = value

    def close(self) -> None:
        self.set(False)


class GpioLed:
    def __init__(self, name: str, pin: int, active_high: bool) -> None:
        from gpiozero import LED  # type: ignore

        self.name = name
        self.pin = pin
        self.led = LED(pin, active_high=active_high)

    def set(self, value: bool) -> None:
        if value:
            self.led.on()
        else:
            self.led.off()

    def close(self) -> None:
        self.led.off()
        self.led.close()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if path.exists():
        user_config = json.loads(path.read_text(encoding="utf-8"))
        deep_update(config, user_config)
    return config


def deep_update(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value


def read_default_gateway() -> str:
    route_path = Path("/proc/net/route")
    if not route_path.exists():
        return ""
    for line in route_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        destination, gateway_hex = parts[1], parts[2]
        if destination != "00000000":
            continue
        gateway_int = int(gateway_hex, 16)
        return socket.inet_ntoa(struct.pack("<L", gateway_int))
    return ""


def command_ok(command: list[str], timeout: float) -> tuple[bool, str]:
    if not command or shutil.which(command[0]) is None:
        return False, f"command not found: {command[0] if command else ''}"
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return result.returncode == 0, output.strip()


def ping_ok(host: str, timeout_seconds: float) -> bool:
    if not host or shutil.which("ping") is None:
        return False
    timeout_arg = max(1, int(timeout_seconds))
    ok, _ = command_ok(["ping", "-c", "1", "-W", str(timeout_arg), host], timeout_seconds + 1)
    return ok


def tcp_ok(host: str, port: int, timeout_seconds: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def dns_ok(name: str, timeout_seconds: float) -> bool:
    if not name:
        return False
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout_seconds)
    try:
        socket.gethostbyname(name)
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(previous_timeout)


def raspberry_connect_ok(config: dict[str, Any]) -> bool:
    command = list(config["raspberry_connect_command"])
    timeout = float(config["raspberry_connect_timeout_seconds"])
    ok, output = command_ok(command, timeout)
    if not ok:
        return False
    lowered = output.lower()
    forbidden = [word.lower() for word in config.get("raspberry_connect_forbidden_words", [])]
    return not any(word in lowered for word in forbidden)


def knx_description_request(host: str, port: int, timeout_seconds: float) -> bool:
    # KNXnet/IP DescriptionRequest: header + HPAI control endpoint.
    packet = bytes([0x06, 0x10, 0x02, 0x03, 0x00, 0x0E, 0x08, 0x01, 0, 0, 0, 0, 0, 0])
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout_seconds)
            sock.bind(("0.0.0.0", 0))
            local_port = sock.getsockname()[1]
            packet = packet[:-2] + struct.pack(">H", local_port)
            sock.sendto(packet, (host, port))
            data, _ = sock.recvfrom(2048)
            return len(data) >= 6 and data[2:4] == bytes([0x02, 0x04])
    except OSError:
        return False


def knx_multicast_search(port: int, timeout_seconds: float) -> bool:
    # KNXnet/IP SearchRequest to 224.0.23.12.
    packet = bytes([0x06, 0x10, 0x02, 0x01, 0x00, 0x0E, 0x08, 0x01, 0, 0, 0, 0, 0, 0])
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.settimeout(timeout_seconds)
            sock.bind(("0.0.0.0", 0))
            local_port = sock.getsockname()[1]
            packet = packet[:-2] + struct.pack(">H", local_port)
            sock.sendto(packet, ("224.0.23.12", port))
            data, _ = sock.recvfrom(2048)
            return len(data) >= 6 and data[2:4] == bytes([0x02, 0x02])
    except OSError:
        return False


def knx_ok(config: dict[str, Any]) -> bool:
    mode = str(config.get("knx_check_mode", "off")).lower()
    host = str(config.get("knx_host", ""))
    port = int(config.get("knx_port", 3671))
    timeout = float(config.get("knx_timeout_seconds", 2))
    if mode == "off":
        return False
    if mode == "host" and host:
        return knx_description_request(host, port, timeout)
    if mode == "multicast":
        return knx_multicast_search(port, timeout)
    return False


def check_status(config: dict[str, Any]) -> Status:
    timeout = float(config["internet_timeout_seconds"])
    local_probe = str(config.get("local_probe_host") or read_default_gateway())
    local_network = ping_ok(local_probe, timeout) if local_probe else False
    internet = tcp_ok(
        str(config["internet_probe_host"]),
        int(config["internet_probe_port"]),
        timeout,
    )
    dns = dns_ok(str(config.get("dns_probe_name", "")), timeout) if internet else False
    return Status(
        raspberry=True,
        local_network=local_network,
        internet=internet,
        dns=dns,
        raspberry_connect=raspberry_connect_ok(config),
        knx=knx_ok(config),
    )


def create_leds(config: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    pins = config["pins"]
    active_high = bool(config.get("active_high", True))
    leds: dict[str, Any] = {}
    for name, pin in pins.items():
        if dry_run:
            leds[name] = MockLed(name, int(pin))
            continue
        try:
            leds[name] = GpioLed(name, int(pin), active_high)
        except Exception as exc:
            logging.warning("No se pudo iniciar GPIO para %s en pin %s: %s", name, pin, exc)
            leds[name] = MockLed(name, int(pin))
    return leds


def apply_leds(leds: dict[str, Any], status: Status, network_blink: bool) -> None:
    leds["raspberry"].set(status.raspberry)
    if status.internet and status.dns:
        leds["network"].set(True)
    elif status.local_network:
        leds["network"].set(network_blink)
    else:
        leds["network"].set(False)
    leds["raspberry_connect"].set(status.raspberry_connect)
    leds["knx"].set(status.knx)


def close_leds(leds: dict[str, Any]) -> None:
    for led in leds.values():
        led.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="KNX Raspberry status LEDs")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Log LED changes instead of using GPIO")
    parser.add_argument("--once", action="store_true", help="Check once, print JSON, then exit")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config(Path(args.config))
    if args.once:
        status = check_status(config)
        print(json.dumps(asdict(status), indent=2, sort_keys=True))
        return 0

    leds = create_leds(config, args.dry_run)
    running = True

    def stop(_signum: int, _frame: Any) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    check_interval = float(config["check_interval_seconds"])
    blink_interval = float(config["blink_interval_seconds"])
    next_check = 0.0
    next_blink = 0.0
    blink_state = False
    status = Status()

    try:
        while running:
            now = time.monotonic()
            if now >= next_check:
                status = check_status(config)
                logging.info("status %s", json.dumps(asdict(status), sort_keys=True))
                next_check = now + check_interval
            if now >= next_blink:
                blink_state = not blink_state
                next_blink = now + blink_interval
            apply_leds(leds, status, blink_state)
            time.sleep(0.1)
    finally:
        close_leds(leds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
