from machine import Pin, UART # UART con GPT físico
import time

# botoncito y led
boton = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin(16, Pin.OUT)

# GPS NEO-6M - descomentar cuando tengamos gps fisico
# gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# NMEA simulada (reemplaza al gps fisico por ahora)
GPS_SIMULADO = "$GPRMC,201530.00,A,1202.784,S,07702.568,W,0.0,0.0,170626,,,A*68"
MODO_SIMULADO = True  # cambiamos a false con gps físico

print("SISTEMA INICIADO")
print("ESPERANDO LA ACTIVACION DEL BOTON DE PANICO...")

def parsear_gprmc(trama):
    partes = trama.split(",")
    if len(partes) < 7: # trama no completa o corrupta
        return None, None, None
    # hora
    raw_hora = partes[1] # formato utc hhmmss
    hora = "{}:{}:{}".format(raw_hora[0:2], raw_hora[2:4], raw_hora[4:6]) # reformateamos
    # latitud
    raw_lat = partes[3]
    hemisferio_lat = partes[4]
    grados_lat = int(raw_lat[0:2])
    minutos_lat = float(raw_lat[2:])
    lat = grados_lat + minutos_lat / 60 # conversion desde grados + minutos decimales
    if hemisferio_lat == "S":
        lat = -lat # latitud negativa para el sur
    # longitud
    raw_lon = partes[5]
    hemisferio_lon = partes[6]
    grados_lon = int(raw_lon[0:3])
    minutos_lon = float(raw_lon[3:]) # 3 digitos para los grados en lugar de 2
    lon = grados_lon + minutos_lon / 60
    if hemisferio_lon == "W":
        lon = -lon # longitud negativa para el oeste
    return round(lat, 6), round(lon, 6), hora

def obtener_gps():
    if MODO_SIMULADO:
        return GPS_SIMULADO
    # gps fisico:
    inicio = time.time()
    while time.time() - inicio < 5: # 5s leyendo UART
        if gps.any():
            linea = gps.readline() # true si hay bytes disponibles
            if linea:
                try:
                    texto = linea.decode('utf-8').strip() # decodificacion byte a texto
                    if texto.startswith("$GPRMC"): # GPRMC es trama posición y hora
                        return texto
                except:
                    pass
    return None

while True:
    if boton.value() == 0:  # boton presionado (PULL_UP: 0 = presionado)
        led.on()
        print("--- BOTON DE PANICO ---")
        print("ALERTA ACTIVADA")
        trama = obtener_gps()
        if trama:
            lat, lon, hora = parsear_gprmc(trama)
            if lat is not None:
                print("Ubicacion GPS:")
                print("  Latitud : {}".format(lat))
                print("  Longitud: {}".format(lon))
                print("  Hora    : {}".format(hora))
                print("Estado  : Alerta enviada")
            else:
                print("GPS: trama invalida")
        else:
            print("GPS: sin senal")
        while boton.value() == 0:
            time.sleep(0.1)
        led.off()
    time.sleep(0.1)
