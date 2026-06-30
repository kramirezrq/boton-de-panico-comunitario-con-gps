"""
============================================================
 BOTON DE PANICO COMUNITARIO CON GPS - VERSION WOKWI
 Raspberry Pi Pico W - MicroPython (simulador wokwi.com)
============================================================

DIFERENCIA CLAVE vs. el codigo de hardware real (main.py):
    Wokwi no tiene un modulo GPS NEO-6M disponible en su catalogo de
    partes, asi que aqui el GPS se REEMPLAZA por un generador de tramas
    NMEA simuladas en software (misma estructura $GPRMC que entrega un
    modulo real). Todo lo demas (boton, LED, buzzer, asyncio, envio a
    Ubidots, reconexion Wi-Fi) es identico a la version de hardware, para
    que la logica que se demuestra en Wokwi sea la misma que corre en la
    Pico W fisica.

USO EN LA DEFENSA:
    Util para mostrar el flujo completo (boton -> GPS -> nube -> alerta)
    cuando no se tiene el hardware GPS a la mano, o como respaldo si
    falla el modulo fisico el dia de la demo.

Wi-Fi en Wokwi: la red simulada se llama "Wokwi-GUEST" y no usa password,
y Wokwi da salida real a internet, por lo que el POST a Ubidots SI llega
al dashboard real.
============================================================
"""

import asyncio
from machine import Pin, PWM
import network
import urequests
import time
import random

# ============================================================
# 1. CONFIGURACION DE HARDWARE (pines del diagram.json)
# ============================================================
BOTON_PIN = 15
LED_PIN = 16
BUZZER_PIN = 17

boton = Pin(BOTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)
buzzer = PWM(Pin(BUZZER_PIN))

# ============================================================
# 2. CONFIGURACION DE RED (Wokwi usa esta red simulada por defecto)
# ============================================================
SSID = "Wokwi-GUEST"
PASSWORD = ""
WIFI_TIMEOUT_S = 15

# ============================================================
# 3. CONFIGURACION UBIDOTS (STEM) - igual que en hardware real
# ============================================================
UBIDOTS_TOKEN = "BBUS-PYzhqV1tKAWE7Dwou2vJ2t3UX5xNZt"
UBIDOTS_DEVICE = "pico-panico"
UBIDOTS_URL = "https://stem.ubidots.com/api/v1.6/devices/" + UBIDOTS_DEVICE + "/"

alerta_pendiente = {"activa": False, "lat": None, "lon": None, "hora": None}

# Punto base para la simulacion: San Isidro, Lima (cambialo si quieren
# simular otro paradero del proyecto)
LAT_BASE = -12.0998
LON_BASE = -77.0388


# ============================================================
# 4. ACTUADORES
# ============================================================
def sonar_buzzer(activar):
    if activar:
        buzzer.freq(2000)
        buzzer.duty_u16(30000)
    else:
        buzzer.duty_u16(0)


def activar_alarma():
    led.on()
    sonar_buzzer(True)


def desactivar_alarma():
    led.off()
    sonar_buzzer(False)


# ============================================================
# 5. RED
# ============================================================
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True
    wlan.connect(SSID, PASSWORD)
    print("Conectando al Wi-Fi (Wokwi-GUEST)...", end="")
    inicio = time.time()
    while not wlan.isconnected():
        if time.time() - inicio > WIFI_TIMEOUT_S:
            print("\nNo se pudo conectar (timeout).")
            return False
        time.sleep(1)
        print(".", end="")
    print("\nConectado! IP:", wlan.ifconfig()[0])
    return True


def hora_a_segundos(hora_str):
    partes = hora_str.split(":")
    return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])


def enviar_a_ubidots(lat, lon, hora):
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    hora_seg = hora_a_segundos(hora)
    payload = (
        '{"latitud":' + str(lat) +
        ',"longitud":' + str(lon) +
        ',"alerta":1' +
        ',"hora_utc":' + str(hora_seg) +
        ',"ubicacion":{"value":1,"context":{"lat":' + str(lat) + ',"lng":' + str(lon) + '}}}'
    )
    print("Enviando:", payload)
    try:
        r = urequests.post(UBIDOTS_URL, data=payload, headers=headers, timeout=10)
        print("Codigo HTTP:", r.status_code)
        r.close()
        return True
    except Exception as e:
        print("Error al enviar a Ubidots:", e)
        return False


# ============================================================
# 6. GPS SIMULADO POR SOFTWARE
# ============================================================
def obtener_gps_simulado():
    """Genera una posicion cercana a LAT_BASE/LON_BASE con un pequeno
    desplazamiento aleatorio, simulando el ruido normal de un GPS real,
    y la hora UTC actual del sistema simulado."""
    lat = round(LAT_BASE + random.uniform(-0.0006, 0.0006), 6)
    lon = round(LON_BASE + random.uniform(-0.0006, 0.0006), 6)
    t = time.localtime()
    hora = "%02d:%02d:%02d" % (t[3], t[4], t[5])
    print("GPS simulado -> Lat:", lat, "Lon:", lon, "Hora:", hora)
    return lat, lon, hora


# ============================================================
# 7. TAREAS ASYNCIO
# ============================================================
async def tarea_boton():
    print("Tarea boton: escuchando...")
    while True:
        if boton.value() == 0 and not alerta_pendiente["activa"]:
            print("\n--- BOTON DE PANICO ACTIVADO (simulacion) ---")
            activar_alarma()
            lat, lon, hora = obtener_gps_simulado()
            alerta_pendiente["activa"] = True
            alerta_pendiente["lat"] = lat
            alerta_pendiente["lon"] = lon
            alerta_pendiente["hora"] = hora
            while boton.value() == 0:
                await asyncio.sleep_ms(100)
        await asyncio.sleep_ms(100)


async def tarea_envio_nube():
    print("Tarea nube: lista.")
    while True:
        if alerta_pendiente["activa"]:
            print("Enviando alerta a Ubidots...")
            ok = enviar_a_ubidots(alerta_pendiente["lat"], alerta_pendiente["lon"], alerta_pendiente["hora"])
            if ok:
                alerta_pendiente["activa"] = False
                desactivar_alarma()
                print("Sistema en espera...")
        await asyncio.sleep_ms(500)


async def tarea_reconexion_wifi():
    wlan = network.WLAN(network.STA_IF)
    while True:
        if not wlan.isconnected():
            print("Wi-Fi caido. Reconectando...")
            conectar_wifi()
        await asyncio.sleep(30)


# ============================================================
# 8. MAIN
# ============================================================
async def main():
    conectar_wifi()
    print("\nSISTEMA INICIADO (WOKWI)")
    print("ESPERANDO BOTON DE PANICO...\n")
    await asyncio.gather(tarea_boton(), tarea_envio_nube(), tarea_reconexion_wifi())


asyncio.run(main())
