# KNX Raspberry Status LEDs

Indicadores LED para maletines KNX con Raspberry Pi.

## Indicadores

El proyecto usa cuatro GPIO de la Raspberry para alimentar directamente cuatro LED de 3,3 V:

| LED | GPIO BCM | Estado |
| --- | ---: | --- |
| Raspberry | 17 | Fijo si el servicio esta vivo |
| Red / Internet | 27 | Apagado sin red, parpadeo con red local, fijo con internet |
| Raspberry Connect | 22 | Fijo si Raspberry Connect parece disponible |
| KNX | 23 | Fijo si la interfaz KNX/IP responde |

Pines fisicos en el conector de 40 pines:

| LED | GPIO BCM | Pin fisico |
| --- | ---: | ---: |
| Raspberry | GPIO17 | 11 |
| Red / Internet | GPIO27 | 13 |
| Raspberry Connect | GPIO22 | 15 |
| KNX | GPIO23 | 16 |
| GND comun | GND | 6, 9, 14, 20, 25, 30, 34 o 39 |

## Cableado

Cada LED se conecta asi:

```text
GPIO ---- resistencia ---- anodo LED
GND  --------------------- catodo LED
```

Recomendacion inicial: resistencia de `470 ohm` o `680 ohm` por LED.

No uses los pines de 5 V para estos LED. Los GPIO de Raspberry trabajan a 3,3 V.

## Instalacion Rapida

En la Raspberry:

```bash
sudo apt update
sudo apt install -y python3-gpiozero

git clone https://github.com/leopitrera/knx-raspi-status-leds.git
cd knx-raspi-status-leds
cp config.example.json config.json
chmod +x install.sh
sudo ./install.sh
```

Edita `config.json` para ajustar la IP de la interfaz KNX/IP si quieres activar el LED KNX.

## Prueba Sin GPIO

```bash
python3 raspi_status_leds.py --dry-run --once
python3 raspi_status_leds.py --dry-run
```

## Servicio

Despues de `install.sh`:

```bash
sudo systemctl status raspi-status-leds.service
sudo journalctl -u raspi-status-leds.service -f
```

Reiniciar:

```bash
sudo systemctl restart raspi-status-leds.service
```

## KNX

El LED KNX puede funcionar de dos maneras:

- `off`: no comprueba KNX.
- `host`: pregunta por UDP a una interfaz KNX/IP concreta.
- `multicast`: busca interfaces KNX/IP en la red usando multicast.

Para empezar, lo mas practico es usar `host` y configurar `knx_host`.
