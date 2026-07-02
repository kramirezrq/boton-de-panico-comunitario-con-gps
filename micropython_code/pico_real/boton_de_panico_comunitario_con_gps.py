import asyncio
from machine import Pin, UART
import network
import urequests
import time

# configuración del hardware
boton = Pin(15, Pin.IN, Pin.PULL_UP)   # botón de pánico
led = Pin(16, Pin.OUT)                 # led indicador
led.off()
buzzer = Pin(14, Pin.OUT)              # buzzer

# configuración del gps
gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# configuración de red
SSID = "karen"
PASSWORD = "26102212"

# configuración de ubidots
UBIDOTS_TOKEN = "BBUS-PYzhqV1tKAWE7Dwou2vJ2t3UX5xNZt"
UBIDOTS_DEVICE = "pico-panico"
UBIDOTS_URL = "https://stem.ubidots.com/api/v1.6/devices/" + UBIDOTS_DEVICE + "/"

# variable compartida
alerta_pendiente = {
    "activa": False,
    "lat": None,
    "lon": None,
    "hora": None
}

# funciones de red
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Wi-Fi ya conectado. IP:", wlan.ifconfig()[0])
        return

    wlan.connect(SSID, PASSWORD)
    print("Conectando al Wi-Fi...", end="")

    while not wlan.isconnected():
        time.sleep(1)
        print(".", end="")

    print("\nConectado! IP:", wlan.ifconfig()[0])


def hora_a_segundos(hora_str):
    partes = hora_str.split(":")
    return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])

def enviar_a_ubidots(lat, lon, hora):
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }

    hora_seg = hora_a_segundos(hora)

    payload = (
        '{"latitud":' + str(lat) +
        ',"longitud":' + str(lon) +
        ',"alerta":1' +
        ',"hora_utc":' + str(hora_seg) +
        ',"ubicacion":{"value":1,"context":{"lat":' + str(lat) + ',"lng":' + str(lon) + '}}}'
    )

    print("Enviando a Ubidots:", payload)

    try:
        r = urequests.post(UBIDOTS_URL, data=payload, headers=headers)
        print("Codigo HTTP:", r.status_code)
        r.close()
    except Exception as e:
        print("Error al enviar a Ubidots:", e)

# funciones del gps

def parsear_gprmc(trama):
    if trama is None:
        return None, None, None

    partes = trama.split(",")

    if len(partes) < 7:
        return None, None, None

    if partes[2] != "A":
        return None, None, None

    try:
        # Hora UTC
        raw_hora = partes[1]
        if len(raw_hora) < 6:
            return None, None, None
        hora = raw_hora[0:2] + ":" + raw_hora[2:4] + ":" + raw_hora[4:6]

        raw_lat = partes[3]
        hemisferio_lat = partes[4]

        if raw_lat == "" or hemisferio_lat == "":
            return None, None, None

        grados_lat = int(raw_lat[0:2])
        minutos_lat = float(raw_lat[2:])
        lat = grados_lat + minutos_lat / 60

        if hemisferio_lat == "S":
            lat = -lat

        raw_lon = partes[5]
        hemisferio_lon = partes[6]

        if raw_lon == "" or hemisferio_lon == "":
            return None, None, None

        grados_lon = int(raw_lon[0:3])
        minutos_lon = float(raw_lon[3:])
        lon = grados_lon + minutos_lon / 60

        if hemisferio_lon == "W":
            lon = -lon

        return round(lat, 6), round(lon, 6), hora

    except Exception as e:
        print("Error al parsear GPRMC:", e)
        return None, None, None


def obtener_gps(timeout_segundos=120):

    print("Buscando señal GPS real...")
    inicio = time.time()
    recibio_tramas = False
    ultimo_mensaje = 0

    led.off()

    while time.time() - inicio < timeout_segundos:
        if gps.any():
            linea = gps.readline()

            if linea:
                try:
                    texto = linea.decode("utf-8").strip()

                    if texto:
                        print(texto)
                        recibio_tramas = True

                    if texto.startswith("$GPRMC"):
                        partes = texto.split(",")

                        if len(partes) > 2:
                            estado = partes[2]

                            if estado == "A":
                                print("GPS válido encontrado.")
                                led.on()   # LED encendido cuando ya tiene fix
                                return texto

                            elif estado == "V":
                                # GPS conectado pero sin fix todavía
                                ahora = time.time()
                                if ahora - ultimo_mensaje > 2:
                                    print("GPS conectado, pero aún sin fix...")
                                    ultimo_mensaje = ahora

                except Exception as e:
                    print("Error leyendo GPS:", e)

        time.sleep_ms(200)

    led.off()

    if recibio_tramas:
        print("El GPS está conectado, pero no consiguió ubicación válida.")
    else:
        print("No se recibieron datos del GPS.")

    return None

# funciones de alerta
async def sonar_buzzer():
    for i in range(10):
        buzzer.on()
        led.on()
        await asyncio.sleep_ms(200)

        buzzer.off()
        led.off()
        await asyncio.sleep_ms(200)

#tareas asincronas
async def tarea_boton():
    print("Tarea boton: escuchando...")

    while True:
        if boton.value() == 0 and not alerta_pendiente["activa"]:
            print("\nBOTON DE PANICO ACTIVADO")

            # Alerta sonora inmediata
            await sonar_buzzer()

            trama = obtener_gps(timeout_segundos=120)

            if trama is None:
                print("No se obtuvo una ubicación real del GPS.")
                print("No se enviará la alerta a Ubidots.")
                led.off()

            else:
                lat, lon, hora = parsear_gprmc(trama)

                if lat is not None:
                    alerta_pendiente["activa"] = True
                    alerta_pendiente["lat"] = lat
                    alerta_pendiente["lon"] = lon
                    alerta_pendiente["hora"] = hora

                    print("GPS VALIDO - COORDENADAS REALES")
                    print("Latitud :", lat)
                    print("Longitud:", lon)
                    print("Hora UTC:", hora)

                else:
                    print("Error: no se pudo parsear la trama GPS.")
                    led.off()

            while boton.value() == 0:
                await asyncio.sleep_ms(100)

        await asyncio.sleep_ms(100)

async def tarea_envio_nube():
    print("Tarea nube: lista.")

    while True:
        if alerta_pendiente["activa"]:
            print("Enviando alerta a Ubidots...")

            enviar_a_ubidots(
                alerta_pendiente["lat"],
                alerta_pendiente["lon"],
                alerta_pendiente["hora"]
            )

            alerta_pendiente["activa"] = False
            alerta_pendiente["lat"] = None
            alerta_pendiente["lon"] = None
            alerta_pendiente["hora"] = None

            print("Sistema en espera...")
            led.off()

        await asyncio.sleep_ms(200)


async def tarea_reconexion_wifi():
    wlan = network.WLAN(network.STA_IF)

    while True:
        if not wlan.isconnected():
            print("Wi-Fi caido. Reconectando...")
            conectar_wifi()

        await asyncio.sleep(30)

#funcion principal
async def main():
    conectar_wifi()

    print("\nSISTEMA INICIADO")
    print("ESPERANDO BOTON DE PANICO...\n")

    await asyncio.gather(
        tarea_boton(),
        tarea_envio_nube(),
        tarea_reconexion_wifi()
    )

asyncio.run(main())
