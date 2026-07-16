# KNX Raspberry Status LEDs

Indicadores LED para maletines KNX con Raspberry Pi.

## Indicadores

El proyecto usa cinco GPIO de la Raspberry para alimentar directamente cinco LED de 3,3 V.
La asignacion recomendada evita los primeros 26 pines porque ahi se monta la Weinzierl KNX BAOS Module 838 kBerry.

| LED | GPIO BCM | Estado |
| --- | ---: | --- |
| Raspberry | 5 | Fijo si el servicio esta vivo |
| Red local | 6 | Fijo si hay red local |
| Internet | 16 | Fijo si hay salida a internet y DNS; parpadea si no |
| Raspberry Connect | 13 | Fijo si Raspberry Connect parece disponible; parpadea si no |
| KNX | 26 | Fijo si la comprobacion KNX responde; parpadea si no |

Los LED de Internet, Raspberry Connect y KNX parpadean cuando su comprobacion falla, en lugar de apagarse, para distinguir "sin servicio" de "LED sin alimentar". La cadencia se ajusta con `blink_interval_seconds` en la configuracion.

Pines fisicos en el conector de 40 pines:

| LED | GPIO BCM | Pin fisico |
| --- | ---: | ---: |
| Raspberry | GPIO5 | 29 |
| Red local | GPIO6 | 31 |
| Internet | GPIO16 | 36 |
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
La comprobacion DNS no tiene LED propio: se usa internamente para que el LED de Internet solo se encienda cuando internet es util por nombre de dominio.

Si instalas el servicio del sistema como `root` y Raspberry Connect esta iniciado en un usuario concreto, configura:

```json
"raspberry_connect_user": "sp4c10"
```

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
En Raspberry Pi 4, es recomendable usar el UART PL011 en esos pines. En MLT001 se ha dejado asi con:

```text
enable_uart=1
dtoverlay=disable-bt
```

Tras reiniciar, `readlink -f /dev/serial0` debe devolver `/dev/ttyAMA0`.
