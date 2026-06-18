"""
gps.py — Lectura y parseo de tramas NMEA del módulo NEO-6M
Conexión: GP0 (TX) → GPS RX | GP1 (RX) ← GPS TX
"""

import time

# Trama NMEA simulada con coordenadas de Lima, Perú
_TRAMA_SIMULADA = "$GPRMC,201530.00,A,1202.784,S,07702.568,W,0.0,0.0,170626,,,A*68"


class GPS:
    """
    Abstracción para el módulo GPS NEO-6M via UART0.
    En modo simulado devuelve coordenadas fijas (Lima, PE).
    """

    def __init__(self, modo_simulado: bool = True, timeout_s: int = 5):
        self.modo_simulado = modo_simulado
        self.timeout_s     = timeout_s
        self._uart         = None

        if not modo_simulado:
            self._iniciar_uart()

    # ── Inicialización ────────────────────────────────────────────────────────

    def _iniciar_uart(self):
        try:
            from machine import UART, Pin
            self._uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
            print("[GPS] UART0 inicializado — NEO-6M conectado")
        except Exception as e:
            print("[GPS] Error al iniciar UART:", e)
            self.modo_simulado = True  # fallback seguro

    # ── API pública ───────────────────────────────────────────────────────────

    def obtener_ubicacion(self):
        """
        Retorna (lat, lon, hora) como floats y string, o None si falla.
        Ejemplo: (-12.046400, -77.042800, "20:15:30")
        """
        trama = self._leer_trama()
        if trama:
            return self._parsear_gprmc(trama)
        return None

    # ── Lectura de trama ──────────────────────────────────────────────────────

    def _leer_trama(self):
        if self.modo_simulado:
            return _TRAMA_SIMULADA

        if self._uart is None:
            return None

        inicio = time.time()
        while time.time() - inicio < self.timeout_s:
            if self._uart.any():
                linea = self._uart.readline()
                if linea:
                    try:
                        texto = linea.decode("utf-8").strip()
                        if texto.startswith("$GPRMC"):
                            return texto
                    except Exception:
                        pass
        print("[GPS] Timeout — sin trama GPRMC en {}s".format(self.timeout_s))
        return None

    # ── Parser NMEA GPRMC ─────────────────────────────────────────────────────

    @staticmethod
    def _parsear_gprmc(trama: str):
        """
        Parsea trama $GPRMC y devuelve (lat, lon, hora).
        $GPRMC,HHMMSS.ss,A,LLLL.LL,a,YYYYY.YY,a,x.x,x.x,DDMMYY,...
        """
        try:
            partes = trama.split(",")
            if len(partes) < 7:
                return None

            # Estado: 'A' = activo, 'V' = vacío/inválido
            if partes[2] != "A":
                print("[GPS] Señal no válida (estado={})".format(partes[2]))
                return None

            # Hora UTC
            raw_hora = partes[1]
            hora = "{}:{}:{}".format(raw_hora[0:2], raw_hora[2:4], raw_hora[4:6])

            # Latitud — formato DDMM.MMMM
            raw_lat        = partes[3]
            hemisferio_lat = partes[4]
            grados_lat     = int(raw_lat[0:2])
            minutos_lat    = float(raw_lat[2:])
            lat            = grados_lat + minutos_lat / 60.0
            if hemisferio_lat == "S":
                lat = -lat

            # Longitud — formato DDDMM.MMMM
            raw_lon        = partes[5]
            hemisferio_lon = partes[6]
            grados_lon     = int(raw_lon[0:3])
            minutos_lon    = float(raw_lon[3:])
            lon            = grados_lon + minutos_lon / 60.0
            if hemisferio_lon == "W":
                lon = -lon

            return round(lat, 6), round(lon, 6), hora

        except Exception as e:
            print("[GPS] Error parseando trama:", e)
            return None
