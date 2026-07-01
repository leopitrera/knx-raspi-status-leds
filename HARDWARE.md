# Guia De Conexion De LEDs

Esta guia describe como conectar cuatro LED/pilotos directamente a los GPIO de una Raspberry Pi, sin alimentacion externa para los LED.

## Resumen

Usaremos cuatro GPIO como salidas digitales a 3,3 V:

| Funcion | GPIO BCM | Pin fisico | Estado esperado |
| --- | ---: | ---: | --- |
| Raspberry encendida | GPIO17 | 11 | Fijo si el servicio esta vivo |
| Red / Internet | GPIO27 | 13 | Apagado sin red, parpadeo con red local, fijo con internet |
| Raspberry Connect | GPIO22 | 15 | Fijo si Connect esta disponible |
| Bus KNX | GPIO23 | 16 | Fijo si hay comunicacion KNX |
| Comun | GND | 6, 9, 14, 20, 25, 30, 34 o 39 | Retorno comun |

## Regla Importante

Los GPIO de Raspberry trabajan a 3,3 V. No conectes 5 V a un GPIO.

Este proyecto alimenta los LED desde GPIO, por tanto:

- No uses el pin de 5 V para alimentar estos LED.
- Cada LED debe llevar limitacion de corriente.
- Si el piloto ya incluye resistencia interna para 3,3/5 V, revisa su consumo antes de conectarlo.

## Material Por Cada Maletin

Para cuatro indicadores:

| Cantidad | Material |
| ---: | --- |
| 4 | LED o piloto LED compatible con 3,3 V |
| 4 | Resistencias de 470 ohm, 1/4 W |
| 1 | Cable GND comun |
| 4 | Cables desde GPIO a LED |
| Opcional | Regleta, clema o conector desmontable para el frontal |

Recomendacion inicial: `470 ohm`.

Alternativas:

| Resistencia | Resultado |
| ---: | --- |
| 330 ohm | Mas brillo, todavia razonable para LED normales |
| 470 ohm | Equilibrada y recomendada para empezar |
| 680 ohm | Menos brillo, mas conservadora |
| 1k ohm | Muy conservadora, suficiente si los LED son de alta eficiencia |

## Conexion De Un LED

Conexion recomendada, encendido con GPIO en alto:

```text
GPIO ---- resistencia ---- anodo LED
GND  --------------------- catodo LED
```

Equivalente por funcion:

```text
Pin 11 / GPIO17 ---- 470R ---- anodo LED Raspberry
GND -------------------------- catodo LED Raspberry

Pin 13 / GPIO27 ---- 470R ---- anodo LED Red/Internet
GND -------------------------- catodo LED Red/Internet

Pin 15 / GPIO22 ---- 470R ---- anodo LED Raspberry Connect
GND -------------------------- catodo LED Raspberry Connect

Pin 16 / GPIO23 ---- 470R ---- anodo LED KNX
GND -------------------------- catodo LED KNX
```

Puedes unir todos los catodos a un mismo GND.

## Polaridad Del LED

En un LED normal:

- Anodo: pata larga, va hacia GPIO mediante la resistencia.
- Catodo: pata corta, va a GND.
- Si el LED no enciende, revisa polaridad antes de cambiar el software.

En un piloto con cables:

- El positivo suele ir al GPIO mediante la resistencia.
- El negativo suele ir a GND.
- Si ya trae resistencia interna y esta marcado como 3,3/5 V, puede funcionar sin resistencia externa, pero es mejor confirmar consumo.

## Que Resistencia Necesito

Formula:

```text
R = (3,3 V - tension_LED) / corriente_LED
```

Ejemplos aproximados con 470 ohm:

| Color LED | Tension aproximada | Corriente con 470 ohm |
| --- | ---: | ---: |
| Rojo | 2,0 V | 2,8 mA |
| Amarillo | 2,1 V | 2,6 mA |
| Verde | 2,1 V | 2,6 mA |
| Azul | 3,0 V | 0,6 mA |
| Blanco | 3,0 V | 0,6 mA |

Para LED azules o blancos puede que `470 ohm` sea tenue. Si necesitas mas brillo, prueba `330 ohm`.

Diseno recomendado:

- Objetivo por LED: 2 a 5 mA.
- Evitar LED de alta potencia o pilotos que pidan mas corriente.
- Si un piloto consume mas de 5 mA desde GPIO, conviene cambiar a transistor, aunque la alimentacion siga siendo de la Raspberry.

## Prueba Manual Antes Del Script

Conecta primero un solo LED, por ejemplo el de Raspberry en GPIO17.

Instala `gpiozero`:

```bash
sudo apt update
sudo apt install -y python3-gpiozero
```

Prueba encendido:

```bash
python3 - <<'PY'
from gpiozero import LED
from time import sleep

led = LED(17)
led.on()
sleep(3)
led.off()
PY
```

Si no enciende:

1. Revisa que usas el pin fisico 11 para GPIO17.
2. Revisa que el catodo va a GND.
3. Revisa la resistencia en serie.
4. Prueba girar el LED si es un LED suelto.

## Instalacion Del Servicio

En la Raspberry:

```bash
sudo apt update
sudo apt install -y git python3-gpiozero

git clone https://github.com/leopitrera/knx-raspi-status-leds.git
cd knx-raspi-status-leds
cp config.example.json config.json
chmod +x install.sh
sudo ./install.sh
```

Ver el servicio:

```bash
sudo systemctl status raspi-status-leds.service
sudo journalctl -u raspi-status-leds.service -f
```

## Configuracion KNX

Edita `config.json`.

Sin comprobacion KNX:

```json
"knx_check_mode": "off"
```

Con interfaz KNX/IP conocida:

```json
"knx_check_mode": "host",
"knx_host": "192.168.1.50",
"knx_port": 3671
```

Busqueda multicast:

```json
"knx_check_mode": "multicast"
```

## Diagnostico Rapido

Ejecutar sin tocar GPIO:

```bash
python3 raspi_status_leds.py --dry-run --once
```

Ejecutar con GPIO, sin instalar servicio:

```bash
python3 raspi_status_leds.py --config config.json
```

## Tabla Final De Estados

| LED | Apagado | Parpadeo | Fijo |
| --- | --- | --- | --- |
| Raspberry | Servicio parado o Raspberry apagada | No usado | Servicio vivo |
| Red / Internet | Sin red local | Red local sin internet | Internet OK |
| Raspberry Connect | Connect no disponible | No usado | Connect OK |
| KNX | KNX no disponible | No usado | KNX OK |
