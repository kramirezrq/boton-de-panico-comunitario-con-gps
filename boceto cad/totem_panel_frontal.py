"""
totem_panel_frontal.py — Script Fusion 360 (API Python)
Genera la pieza: PANEL FRONTAL del tótem con:
  - Hueco circular para el botón antivandálico (∅ 22 mm)
  - Hueco para baliza LED (∅ 16 mm)
  - Placa de acrílico 3 mm de espesor

Cómo ejecutar:
  Fusion 360 → Utilidades → Scripts y complementos → Scripts → Ejecutar
  Seleccionar este archivo .py
"""

import adsk.core
import adsk.fusion
import traceback
import math

# ─── Parámetros editables ─────────────────────────────────────────────────────
PANEL_W        = 200    # mm — ancho del panel (igual al de la columna × 2.5)
PANEL_H        = 250    # mm — alto del panel
PANEL_ESP      = 3      # mm — espesor
BOTON_DIAM     = 22     # mm — diámetro hueco botón antivandálico M22
BOTON_X        = 100    # mm — posición X del centro del botón (mitad panel)
BOTON_Y        = 140    # mm — posición Y del centro del botón
LED_DIAM       = 16     # mm — diámetro hueco baliza LED
LED_X          = 100    # mm
LED_Y          = 80     # mm
RADIO_ESQUINAS = 5      # mm — radio de esquinas del panel (aspecto moderno)


def _circulo(sketch, cx, cy, diam):
    """Dibuja un círculo centrado en (cx, cy) con el diámetro indicado."""
    centro = adsk.core.Point3D.create(cx, cy, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(centro, diam / 2)


def run(context):
    ui = None
    try:
        app  = adsk.core.Application.get()
        ui   = app.userInterface
        des  = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent

        sketches = root.sketches
        xy_plane = root.xYConstructionPlane
        extrudes = root.features.extrudeFeatures

        # ── 1. Silueta del panel (rectángulo) ────────────────────────────────
        sk_panel = sketches.add(xy_plane)
        lines    = sk_panel.sketchCurves.sketchLines

        p0 = adsk.core.Point3D.create(0,        0,        0)
        p1 = adsk.core.Point3D.create(PANEL_W,  0,        0)
        p2 = adsk.core.Point3D.create(PANEL_W,  PANEL_H,  0)
        p3 = adsk.core.Point3D.create(0,        PANEL_H,  0)

        lines.addByTwoPoints(p0, p1)
        lines.addByTwoPoints(p1, p2)
        lines.addByTwoPoints(p2, p3)
        lines.addByTwoPoints(p3, p0)

        # ── 2. Huecos en el mismo sketch ─────────────────────────────────────
        _circulo(sk_panel, BOTON_X, BOTON_Y, BOTON_DIAM)
        _circulo(sk_panel, LED_X,   LED_Y,   LED_DIAM)

        # Seleccionar solo el perfil exterior (índice 0 = más grande)
        # Los perfiles interiores son los huecos — Fusion los resta automáticamente
        # al hacer extrude con el perfil con huecos seleccionado.
        prof_panel = None
        for i in range(sk_panel.profiles.count):
            p = sk_panel.profiles.item(i)
            bb = p.boundingBox
            area_w = abs(bb.maxPoint.x - bb.minPoint.x)
            area_h = abs(bb.maxPoint.y - bb.minPoint.y)
            if area_w > PANEL_W * 0.8 and area_h > PANEL_H * 0.8:
                prof_panel = p
                break

        if prof_panel is None:
            prof_panel = sk_panel.profiles.item(0)

        ext_in = extrudes.createInput(
            prof_panel,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        dist = adsk.core.ValueInput.createByReal(PANEL_ESP / 10)
        ext_in.setDistanceExtent(False, dist)
        ext   = extrudes.add(ext_in)
        ext.bodies.item(0).name = "Panel_Frontal_Totem"

        ui.messageBox(
            "✅ Panel frontal generado:\n"
            "  • Tamaño: {}×{} mm, espesor {} mm\n"
            "  • Hueco botón M22 en ({}, {})\n"
            "  • Hueco baliza LED en ({}, {})".format(
                PANEL_W, PANEL_H, PANEL_ESP,
                BOTON_X, BOTON_Y,
                LED_X,   LED_Y
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Error:\n{}".format(traceback.format_exc()))
