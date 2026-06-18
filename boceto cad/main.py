"""
Botón de Pánico Comunitario con GPS
Curso: Arquitectura del Computador I — Código 16953
Universidad ESAN — Semestre 2026-1
Profesor: Marks Calderón Niquin

Punto de entrada principal.
Integra lectura de botón, GPS y (Semana 2) publicación MQTT.
"""

import time
import asyncio
from boton import Boton
from gps import GPS

# ─── Configuración de pines ───────────────────────────────────────────────────
PIN_BOTON  = 15   # GPIO15 — botón antivandálico (PULL_UP)
PIN_BALIZA = 16   # GPIO16 — baliza LED de alerta

# ─── Modo simulado (True = sin hardware GPS físico) ───────────────────────────
MODO_SIMULADO = True

# ─── MQTT (habilitar en Semana 2) ─────────────────────────────────────────────
MQTT_HABILITADO = False
MQTT_BROKER     = "broker.hivemq.com"
MQTT_PUERTO     = 1883
MQTT_TOPIC      = "panico/lima/alerta"
MQTT_CLIENTE_ID = "pico_totem_01"

# ─── Instancias ───────────────────────────────────────────────────────────────
boton  = Boton(PIN_BOTON, PIN_BALIZA)
sensor = GPS(modo_simulado=MODO_SIMULADO)

# ─── MQTT (stub para Semana 2) ────────────────────────────────────────────────
mqtt_client = None

def conectar_mqtt():
    """Conecta al broker MQTT. Activar en Semana 2."""
    global mqtt_client
    try:
        from umqtt.simple import MQTTClient
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect("TU_SSID", "TU_PASSWORD")
        timeout = 10
        while not wlan.isconnected() and timeout:
            time.sleep(1)
            timeout -= 1
        if wlan.isconnected():
            mqtt_client = MQTTClient(MQTT_CLIENTE_ID, MQTT_BROKER, MQTT_PUERTO)
            mqtt_client.connect()
            print("[MQTT] Conectado a", MQTT_BROKER)
        else:
            print("[MQTT] Sin Wi-Fi — operando sin conectividad")
    except Exception as e:
        print("[MQTT] Error:", e)


def publicar_alerta(lat, lon, hora):
    """Publica la alerta al broker MQTT."""
    if mqtt_client is None:
        return
    payload = '{{"lat":{:.6f},"lon":{:.6f},"hora":"{}","totem":"totem_01"}}'.format(
        lat, lon, hora
    )
    try:
        mqtt_client.publish(MQTT_TOPIC, payload)
        print("[MQTT] Alerta publicada:", payload)
    except Exception as e:
        print("[MQTT] Error al publicar:", e)


# ─── Bucle principal ──────────────────────────────────────────────────────────
def main():
    print("=" * 45)
    print("  SISTEMA DE BOTÓN DE PÁNICO — PICO W")
    print("  Universidad ESAN | Arq. Computador I")
    print("=" * 45)

    if MQTT_HABILITADO:
        conectar_mqtt()

    print("\n[OK] Esperando activación del botón...\n")

    while True:
        if boton.presionado():
            boton.activar_baliza()
            print("\n!!! BOTÓN DE PÁNICO ACTIVADO !!!")

            datos = sensor.obtener_ubicacion()

            if datos:
                lat, lon, hora = datos
                print("[GPS] Lat: {:.6f} | Lon: {:.6f} | Hora: {}".format(lat, lon, hora))
                if MQTT_HABILITADO:
                    publicar_alerta(lat, lon, hora)
                else:
                    print("[INFO] MQTT deshabilitado — alerta local registrada")
            else:
                print("[GPS] Sin señal — reintentando en próximo ciclo")

            boton.esperar_liberacion()
            boton.desactivar_baliza()
            print("[OK] Sistema listo para nueva alerta\n")

        time.sleep(0.1)


if __name__ == "__main__":
    main()
