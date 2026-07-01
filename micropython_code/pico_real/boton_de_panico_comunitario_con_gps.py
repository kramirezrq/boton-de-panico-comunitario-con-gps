# definir librerias
import asyncio          # corremos tareas al mismo tiempo
from machine import Pin, UART   # controlamos los gpio y nos comunicamos con el gps
import network          # gestionamos la conexión wifi
import urequests        # enviamos datos a ubidots mediante http
import time             # controlamos tiempos y pausas

# configuracion de hardware
boton = Pin(15, Pin.IN, Pin.PULL_UP)   # configuramos el botón como entrada con resistencia pull-up
led = Pin(16, Pin.OUT)                 # configuramos el led como salida
led.off() 
buzzer = Pin(14, Pin.OUT)              # configuramos el buzzer como salida

# configuración del gps
gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))   # configuramos la comunicación uart con el módulo gps
GPS_SIMULADO = "$GPRMC,201530.00,A,1202.784,S,07702.568,W,0.0,0.0,170626,,,A*68"   # definimos una trama gps simulada como respaldo

# configuración de red
SSID = "karen"          # definimos el nombre de la red wifi
PASSWORD = "26102212"   # definimos la contraseña de la red wifi

# configuración de ubidots
UBIDOTS_TOKEN = "BBUS-PYzhqV1tKAWE7Dwou2vJ2t3UX5xNZt"   # definimos el token de autenticación
UBIDOTS_DEVICE = "pico-panico"                        # definimos el nombre del dispositivo
UBIDOTS_URL = "https://stem.ubidots.com/api/v1.6/devices/" + UBIDOTS_DEVICE + "/"   # definimos la url para enviar los datos

# variable compartida entre tareas
alerta_pendiente = {"activa": False, "lat": None, "lon": None, "hora": None}   # almacenamos temporalmente los datos de la alerta

# funciones de red
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)      # creamos la interfaz wifi en modo estación
    wlan.active(True)                        # activamos la interfaz wifi
    if wlan.isconnected():
        return                               # verificamos si ya existe conexión
    wlan.connect(SSID, PASSWORD)             # conectamos a la red wifi
    print("Conectando al Wi-Fi...", end="")
    while not wlan.isconnected():
        time.sleep(1)                        # esperamos hasta establecer la conexión
        print(".", end="")
    print("\nConectado! IP:", wlan.ifconfig()[0])   # mostramos la dirección ip asignada

def hora_a_segundos(hora_str):
    partes = hora_str.split(":")             # separamos la hora en horas, minutos y segundos
    return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])   # convertimos la hora a segundos

def enviar_a_ubidots(lat, lon, hora):
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,        # definimos el token de autenticación
        "Content-Type": "application/json"    # definimos el formato de los datos
    }
    hora_seg = hora_a_segundos(hora)          # convertimos la hora a segundos
    payload = (
        '{"latitud":' + str(lat) +
        ',"longitud":' + str(lon) +
        ',"alerta":1' +
        ',"hora_utc":' + str(hora_seg) +
        ',"ubicacion":{"value":1,"context":{"lat":' + str(lat) + ',"lng":' + str(lon) + '}}}'
    )                                         # construimos el mensaje en formato json

    print("Enviando:", payload)

    try:
        r = urequests.post(UBIDOTS_URL, data=payload, headers=headers)   # enviamos los datos a ubidots
        print("Codigo HTTP:", r.status_code)                             # mostramos el estado de la solicitud
        r.close()                                                        # cerramos la conexión
    except Exception as e:
        print("Error al enviar:", e)                                     # mostramos el error si ocurre

# funciones del gps
def parsear_gprmc(trama):
    partes = trama.split(",")                    # separamos la trama en sus diferentes campos
    if len(partes) < 7:
        return None, None, None                  # verificamos que la trama sea válida

    # obtenemos la hora utc
    raw_hora = partes[1]
    hora = raw_hora[0:2] + ":" + raw_hora[2:4] + ":" + raw_hora[4:6]

    # obtenemos la latitud
    raw_lat = partes[3]
    hemisferio_lat = partes[4]
    grados_lat = int(raw_lat[0:2])
    minutos_lat = float(raw_lat[2:])
    lat = grados_lat + minutos_lat / 60          # convertimos a grados decimales
    if hemisferio_lat == "S":
        lat = -lat                               # asignamos signo negativo al hemisferio sur

    # obtenemos la longitud
    raw_lon = partes[5]
    hemisferio_lon = partes[6]
    grados_lon = int(raw_lon[0:3])
    minutos_lon = float(raw_lon[3:])
    lon = grados_lon + minutos_lon / 60          # convertimos a grados decimales
    if hemisferio_lon == "W":
        lon = -lon                               # asignamos signo negativo al hemisferio oeste

    return round(lat, 6), round(lon, 6), hora    # devolvemos la latitud, longitud y hora

async def obtener_gps():
    print("Buscando señal GPS...")

    inicio = time.time()                         # registramos el tiempo de inicio

    while time.time() - inicio < 5:              # esperamos hasta 5 segundos

        if gps.any():                            # verificamos si hay datos disponibles

            linea = gps.readline()               # leemos una línea del gps

            if linea:

                try:
                    texto = linea.decode("utf-8").strip()   # convertimos la trama a texto

                    print(texto)

                    if texto.startswith("$GPRMC"):          # verificamos que sea una trama gprmc

                        partes = texto.split(",")

                        if len(partes) > 2 and partes[2] == "A":
                            print("GPS válido encontrado.")
                            return texto                   # devolvemos la trama válida

                except Exception:
                    pass                                   # ignoramos errores de lectura

        await asyncio.sleep_ms(100)                       # esperamos antes de volver a leer, sin bloquear las demás tareas

    print("No se obtuvo GPS válido.")
    return GPS_SIMULADO                                   # utilizamos la trama simulada como respaldo

async def sonar_buzzer():
    for i in range(10):                   # repetimos el sonido 10 veces
        buzzer.on()                       # activamos el buzzer
        led.on()                          # encendemos el led
        await asyncio.sleep_ms(200)       # mantenemos el sonido durante 200 ms

        buzzer.off()                      # desactivamos el buzzer
        led.off()                         # apagamos el led
        await asyncio.sleep_ms(200)       # esperamos 200 ms antes del siguiente pitido

# tareas asíncronas

async def tarea_boton():
    print("Tarea boton: escuchando...")
    while True:                                               # mantenemos la tarea en ejecución
        if boton.value() == 0 and not alerta_pendiente["activa"]:   # detectamos la pulsación del botón
            print("\n--- BOTON DE PANICO ACTIVADO ---")

            await sonar_buzzer()                              # activamos la alarma sonora

            trama = await obtener_gps()                       # obtenemos la trama del gps
            lat, lon, hora = parsear_gprmc(trama)             # extraemos la latitud, longitud y hora

            if lat is not None:
                alerta_pendiente["activa"] = True             # activamos la alerta pendiente
                alerta_pendiente["lat"] = lat                 # almacenamos la latitud
                alerta_pendiente["lon"] = lon                 # almacenamos la longitud
                alerta_pendiente["hora"] = hora               # almacenamos la hora
                print("Alerta -> Lat:", lat, "Lon:", lon, "Hora:", hora)
            else:
                print("Error: no se pudo parsear la trama GPS.")
                led.off()                                     # apagamos el led si ocurre un error

            while boton.value() == 0:
                await asyncio.sleep_ms(100)                   # esperamos a que se libere el botón

        await asyncio.sleep_ms(100)                           # evitamos lecturas continuas

async def tarea_envio_nube():
    print("Tarea nube: lista.")
    while True:                                               # mantenemos la tarea en ejecución
        if alerta_pendiente["activa"]:                        # verificamos si existe una alerta pendiente
            print("Enviando alerta a Ubidots...")
            enviar_a_ubidots(
                alerta_pendiente["lat"],
                alerta_pendiente["lon"],
                alerta_pendiente["hora"]
            )                                                 # enviamos los datos a ubidots

            alerta_pendiente["activa"] = False                # restablecemos el estado de la alerta
            alerta_pendiente["lat"] = None                    # limpiamos la latitud
            alerta_pendiente["lon"] = None                    # limpiamos la longitud
            alerta_pendiente["hora"] = None                   # limpiamos la hora

            led.off()                                         # apagamos el led
            print("Sistema en espera...")

        await asyncio.sleep_ms(200)                           # esperamos antes de verificar nuevamente

async def tarea_reconexion_wifi():
    wlan = network.WLAN(network.STA_IF)                       # obtenemos la interfaz wifi
    while True:                                               # mantenemos la tarea en ejecución
        if not wlan.isconnected():
            print("Wi-Fi caido. Reconectando...")
            conectar_wifi()                                   # restablecemos la conexión wifi

        await asyncio.sleep(30)                               # verificamos la conexión cada 30 segundos

# función principal
async def main():
    conectar_wifi()                           # establecemos la conexión wifi
    print("\nSISTEMA INICIADO")
    print("ESPERANDO BOTON DE PANICO...\n")

    await asyncio.gather(                     # ejecutamos las tareas de forma concurrente
        tarea_boton(),
        tarea_envio_nube(),
        tarea_reconexion_wifi()
    )

asyncio.run(main())                           # iniciamos la ejecución del programa
