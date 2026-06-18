"""
boton.py — Lectura del botón antivandálico y control de la baliza LED
Conexión:
  GP15 → Botón antivandálico (PULL_UP interno — GND al presionar)
  GP16 → Baliza LED (330 Ω en serie)
"""

import time

try:
    from machine import Pin
    _HW_DISPONIBLE = True
except ImportError:
    _HW_DISPONIBLE = False
    print("[BOTON] machine.Pin no disponible — modo mock activado")


class _PinMock:
    """Stub para pruebas sin hardware."""
    def __init__(self, *args, **kwargs):
        self._val = 1  # reposo = 1 (PULL_UP)

    def value(self, v=None):
        if v is None:
            return self._val
        self._val = v

    def on(self):
        self._val = 1

    def off(self):
        self._val = 0


class Boton:
    """
    Maneja el botón antivandálico (lógica activa-baja con PULL_UP)
    y la baliza LED de alerta.

    Parámetros
    ----------
    pin_boton  : int  — GPIO del botón (default 15)
    pin_baliza : int  — GPIO de la baliza LED (default 16)
    debounce_ms: int  — retardo anti-rebote en ms (default 50)
    """

    def __init__(self, pin_boton: int = 15, pin_baliza: int = 16, debounce_ms: int = 50):
        self.debounce_ms = debounce_ms

        if _HW_DISPONIBLE:
            self._boton  = Pin(pin_boton,  Pin.IN,  Pin.PULL_UP)
            self._baliza = Pin(pin_baliza, Pin.OUT)
        else:
            self._boton  = _PinMock()
            self._baliza = _PinMock()

        self._baliza.off()
        print("[BOTON] Inicializado — GP{} (botón) | GP{} (baliza)".format(
            pin_boton, pin_baliza
        ))

    # ── API pública ───────────────────────────────────────────────────────────

    def presionado(self) -> bool:
        """
        Retorna True si el botón está presionado (con anti-rebote).
        PULL_UP → presionado = 0.
        """
        if self._boton.value() == 0:
            time.sleep_ms(self.debounce_ms)          # anti-rebote
            return self._boton.value() == 0          # confirmar
        return False

    def esperar_liberacion(self):
        """Bloquea hasta que el botón sea soltado."""
        while self._boton.value() == 0:
            time.sleep_ms(50)

    def activar_baliza(self):
        """Enciende la baliza LED de alerta."""
        self._baliza.on()
        print("[BALIZA] Encendida")

    def desactivar_baliza(self):
        """Apaga la baliza LED de alerta."""
        self._baliza.off()
        print("[BALIZA] Apagada")

    def parpadeo_baliza(self, veces: int = 3, periodo_ms: int = 300):
        """
        Hace parpadear la baliza N veces.
        Útil para confirmar recepción de alerta.
        """
        for _ in range(veces):
            self._baliza.on()
            time.sleep_ms(periodo_ms)
            self._baliza.off()
            time.sleep_ms(periodo_ms)
