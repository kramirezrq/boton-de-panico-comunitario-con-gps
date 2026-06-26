from machine import Pin, UART
import network
import socket
import time

# --- 1. CONFIGURACIÓN DE HARDWARE ---
boton = Pin(15, Pin.IN, Pin.PULL_UP)
led = Pin(16, Pin.OUT)

# GPS
gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
GPS_SIMULADO = "$GPRMC,201530.00,A,1202.784,S,07702.568,W,0.0,0.0,170626,,,A*68"

# --- 2. CONFIGURACIÓN DE RED & SERVIDOR ---
SSID = "SONIA"
PASSWORD = "ssjj0211"
LAPTOP_IP = "192.168.1.8"
PORT = 5000

# --- 3. FUNCIONES DE RED ---
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print("Conectando al Wi-Fi...", end="")
    while not wlan.isconnected():
        time.sleep(1)
        print(".", end="")
    
    print("\n¡Conectado al Wi-Fi!")
    print("Datos de red:", wlan.ifconfig())

def enviar_datos_servidor(mensaje):
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((LAPTOP_IP, PORT))
        print(f"Enviando al servidor: {mensaje}")
        s.send(mensaje.encode('utf-8'))
        
        respuesta = s.recv(1024)
        print(f"Respuesta del servidor: {respuesta.decode('utf-8')}")
    except Exception as e:
        print("Error de red al enviar datos:", e)
    finally:
        if s:
            s.close()

# --- 4. FUNCIONES DE GPS ---
def parsear_gprmc(trama):
    partes = trama.split(",")
    if len(partes) < 7:
        return None, None, None
    
    # Hora UTC
    raw_hora = partes[1]
    hora = "{}:{}:{}".format(raw_hora[0:2], raw_hora[2:4], raw_hora[4:6])
    
    # Latitud
    raw_lat = partes[3]
    hemisferio_lat = partes[4]
    grados_lat = int(raw_lat[0:2])
    minutos_lat = float(raw_lat[2:])
    lat = grados_lat + minutos_lat / 60
    if hemisferio_lat == "S":
        lat = -lat
        
    # Longitud
    raw_lon = partes[5]
    hemisferio_lon = partes[6]
    grados_lon = int(raw_lon[0:3])
    minutos_lon = float(raw_lon[3:])
    lon = grados_lon + minutos_lon / 60
    if hemisferio_lon == "W":
        lon = -lon
        
    return round(lat, 6), round(lon, 6), hora

def obtener_gps():
    # 1. Verificar si hay datos reales en el buffer del GPS físico
    if gps.any():
        print("-> Datos detectados en GPS físico. Leyendo...")
        inicio = time.time()
        # Intentamos capturar la trama GPRMC durante 3 segundos
        while time.time() - inicio < 3:
            if gps.any():
                linea = gps.readline()
                if linea:
                    try:
                        texto = linea.decode('utf-8').strip()
                        if texto.startswith("$GPRMC"):
                            return texto
                    except:
                        pass
        print("-> GPS físico conectado pero no se encontró una trama $GPRMC válida.")
    
    # 2. Si gps.any() es falso (o no se pudo parsear una trama real), usa el string por defecto
    print("-> GPS físico sin datos (gps.any() es falso). Usando string por defecto.")
    return GPS_SIMULADO

# --- 5. FLUJO PRINCIPAL ---
conectar_wifi()

print("\nSISTEMA INICIADO Y RED LISTA")
print("ESPERANDO LA ACTIVACION DEL BOTON DE PANICO...")

while True:
    if boton.value() == 0: 
        led.on() 
        print("\n--- BOTON DE PANICO ACTIVADO ---")
        
        trama = obtener_gps()
        lat, lon, hora = parsear_gprmc(trama)
        
        if lat is not None:
            mensaje_alerta = f"Hora:{hora} - ALERTA PANICO - Lat:{lat}, Lon:{lon}"
            print(mensaje_alerta)
            enviar_datos_servidor(mensaje_alerta)
        else:
            print("Error: No se pudo parsear la trama de respaldo.")
            enviar_datos_servidor("ALERTA PANICO - Error en datos de ubicacion")
            
        # Antirebote: Espera a que sueltes el botón
        while boton.value() == 0:
            time.sleep(0.1)
            
        led.off()  # Apaga foco al soltarlo
        print("Sistema en espera de nuevo...")
        
    time.sleep(0.1)