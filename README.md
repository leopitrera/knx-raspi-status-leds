# KNX Raspberry Status LEDs

Indicadores LED para maletines KNX con Raspberry Pi.

## Indicadores

El proyecto usa cuatro GPIO de la Raspberry para alimentar directamente cuatro LED de 3,3 V.
La asignacion recomendada evita los primeros 26 pines porque ahi se monta la Weinzierl KNX BAOS Module 838 kBerry.

| LED | GPIO BCM | Estado |
| --- | ---: | --- |
| Raspberry | 5 | Fijo si el servicio esta vivo |
| Red / Internet | 6 | Apagado sin red, parpadeo con red local, fijo con internet |
| Raspberry Connect | 13 | Fijo si Raspberry Connect parece disponible |
| KNX | 26 | Fijo si la comprobacion KNX responde |

Pines fisicos en el conector de 40 pines:

| LED | GPIO BCM | Pin fisico |
| --- | ---: | ---: |
| Raspberry | GPIO5 | 29 |
| Red / Internet | GPIO6 | 31 |
| Raspberry Connect | GPIO13 | 33 |
| KNX | GPIO26 | 37 |
| GND comun | GND | 39 recomendado; 30 o 34 tambien disponibles |

## Cableado

Cada LED se conecta asi:

```text
GPIO ---- resistencia ---- anodo LED
GND  --------------------- catodo LED
```

Recomendacion inicial: resistencia de `470 ohm` o `680 ohm` por LED.

No uses los pines de 5 V para estos LED. Los GPIO de Raspberry trabajan a 3,3 V.

Consulta la guia completa de cableado, resistencias y prueba manual en [HARDWARE.md](HARDWARE.md).

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

Edita `config.json` para ajustar el modo de comprobacion KNX si quieres activar el LED KNX.

Si no quieres usar `sudo`, puedes instalarlo como servicio de usuario:

```bash
git clone https://github.com/leopitrera/knx-raspi-status-leds.git
cd knx-raspi-status-leds
chmod +x install-user.sh
./install-user.sh
```

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

## Weinzierl kBerry Y KNX

La Weinzierl KNX BAOS Module 838 kBerry se pincha en el conector GPIO y usa comunicacion serie UART.
Segun la ficha tecnica, su interfaz host usa los pines fisicos 1, 6, 8 y 10. Por eso los LED se han movido a los pines fisicos 29, 31, 33 y 37, que quedan fuera de la zona del conector de 26 pines.

El LED KNX puede comprobar varias interfaces:

- `off`: no comprueba KNX.
- `host`: pregunta por UDP a una interfaz KNX/IP concreta.
- `multicast`: busca interfaces KNX/IP en la red usando multicast.
- `serial`: pregunta a la Weinzierl kBerry por UART/BAOS y enciende el LED si el item BAOS de estado de bus indica conexion.

Para la kBerry en Raspberry Pi:

```json
"knx_check_mode": "serial",
"knx_serial_device": "/dev/serial0",
"knx_serial_baudrate": 19200
```

La consola/login serie de Raspberry debe estar desactivada para que la kBerry tenga libre el UART de los pines 8 y 10.
