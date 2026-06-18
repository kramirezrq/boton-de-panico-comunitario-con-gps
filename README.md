# Botón de Pánico Comunitario con GPS

Sistema embebido IoT basado en Raspberry Pi Pico W que permite a los ciudadanos activar una alerta de emergencia desde un tótem en paraderos públicos. Al presionar el botón, el sistema captura la ubicación GPS en tiempo real y la publica en un mapa web compartido vía MQTT, notificando a los agentes de seguridad más cercanos.

## Equipo

| Nombre | Rol |
|---|---|
| Sergio Giovanni Jacobo Jauregui | Por definir |
| Leo Junior Rimachi Aroni | Por definir |
| Karen Noelia Ramirez Quevedo | Por definir |
| Jean Pierre Alexander Levano Martel | Por definir |

**Curso:** Arquitectura del Computador I — Código 16953  
**Semestre:** 2026-1  
**Profesor:** Marks Calderón Niquin

---

## Problema

En zonas urbanas de Lima, los paraderos de transporte público son puntos de alta incidencia de robos, acoso y situaciones de emergencia. Los ciudadanos no cuentan con un mecanismo físico, inmediato y geolocalizad para pedir ayuda sin depender de un celular (que puede haber sido robado o no tener señal).

## Usuario objetivo

Personas que usan el transporte público en paraderos urbanos y que necesitan solicitar ayuda de forma rápida, visible y sin fricción, especialmente adultos mayores, estudiantes y personas en situación de vulnerabilidad.

---

## Solución

Un tótem físico instalado en el paradero con un botón antivandálico protegido. Al presionarlo:

1. El GPS NEO-6M captura las coordenadas exactas del tótem.
2. Una baliza LED se activa como señal visual de alerta.
3. El sistema publica la ubicación y hora del evento a un mapa web compartido vía MQTT.
4. Los agentes de seguridad suscritos reciben la alerta en tiempo real.

---

## Hardware

| Componente | Interfaz | Función |
|---|---|---|
| Raspberry Pi Pico W | — | Microcontrolador principal |
| Botón antivandálico | GPIO digital | Activación de alerta |
| GPS NEO-6M | UART | Captura de coordenadas |
| Baliza LED | GPIO digital | Señal visual de alerta activa |

## Diagrama de conexiones

```
Pico W
├── GP0 (UART0 TX) ──► GPS NEO-6M (RX)
├── GP1 (UART0 RX) ◄── GPS NEO-6M (TX)
├── GP15           ──► Botón antivandálico (+ resistencia pull-down)
└── GP14           ──► Baliza LED (+ resistencia 330Ω)
```

> El diagrama detallado en imagen se encuentra en (https://wokwi.com/projects/467182323124193281).

---

## Estructura del repositorio

```
boton-panico-gps/
├── README.md
├── src/
│   ├── main.py          # punto de entrada, lógica principal
│   ├── gps.py           # lectura y parseo de tramas NMEA del NEO-6M
│   └── boton.py         # lectura del botón y control de la baliza
├── hardware/
│   └── diagrama_conexiones.png
└── cad/
    └── totem_boceto.png  # boceto preliminar de la pieza 3D
```

---

## Requisitos

- Raspberry Pi Pico W
- MicroPython v1.22 o superior
- Módulo GPS NEO-6M
- Botón antivandálico (NO)
- Baliza LED 12V (o LED estándar para prototipo)

---

## Estado del proyecto

| Semana | Entregable | Estado |
|---|---|---|
| 1 | Lectura de botón + GPS en protoboard, README y boceto 3D | En curso |
| 2 | Conectividad Wi-Fi, MQTT, dashboard y asyncio | Pendiente |
| 3 | Integración completa, pieza 3D impresa, paper y defensa | Pendiente |

---

## Licencia

Proyecto académico — Universidad ESAN 2026-1.
