from machine import Pin, UART
import time

boton = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin(16, Pin.OUT)
buzzer = Pin(14, Pin.OUT)

# gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

GPS_SIMULADO = "$GPRMC,201530.00,A,1202.784,S,07702.568,W,0.0,0.0,170626,,,A*68"
MODO_SIMULADO = True

print("SISTEMA INICIADO")
print("ESPERANDO LA ACTIVACION DEL BOTON DE PANICO...")

def parsear_gprmc(trama):
    partes = trama.split(",")
    if len(partes) < 7:
        return None, None, None

    raw_hora = partes[1]
    hora = "{}:{}:{}".format(raw_hora[0:2], raw_hora[2:4], raw_hora[4:6])

    raw_lat = partes[3]
    hemisferio_lat = partes[4]
    grados_lat = int(raw_lat[0:2])
    minutos_lat = float(raw_lat[2:])
    lat = grados_lat + minutos_lat / 60
    if hemisferio_lat == "S":
        lat = -lat

    raw_lon = partes[5]
    hemisferio_lon = partes[6]
    grados_lon = int(raw_lon[0:3])
    minutos_lon = float(raw_lon[3:])
    lon = grados_lon + minutos_lon / 60
    if hemisferio_lon == "W":
        lon = -lon

    return round(lat, 6), round(lon, 6), hora

def obtener_gps():
    if MODO_SIMULADO:
        return GPS_SIMULADO

    inicio = time.time()
    while time.time() - inicio < 5:
        if gps.any():
            linea = gps.readline()
            if linea:
                try:
                    texto = linea.decode("utf-8").strip()
                    if texto.startswith("$GPRMC"):
                        return texto
                except:
                    pass
    return None

while True:
    if boton.value() == 0:
        print("--- BOTON DE PANICO ---")
        print("ALERTA ACTIVADA")

        for i in range(10):
            led.on()
            buzzer.on()
            time.sleep(0.2)
            led.off()
            buzzer.off()
            time.sleep(0.2)

        trama = obtener_gps()

        if trama:
            lat, lon, hora = parsear_gprmc(trama)

            if lat is not None:
                print("Ubicacion GPS:")
                print("  Latitud : {}".format(lat))
                print("  Longitud: {}".format(lon))
                print("  Hora    : {}".format(hora))
                print("Estado: Alerta enviada")
            else:
                print("GPS: trama invalida")
        else:
            print("GPS: sin senal")

        while boton.value() == 0:
            time.sleep(0.1)

    time.sleep(0.1)