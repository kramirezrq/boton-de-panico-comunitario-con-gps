"""
totem_caja_electronica.py — Script Fusion 360 (API Python)
Genera la pieza: CAJA INTERNA para electrónica del tótem.
  - Compartimiento para Raspberry Pi Pico W (51 × 21 mm)
  - Compartimiento para módulo GPS NEO-6M (25 × 25 mm)
  - Guías de PCB laterales de 2 mm
  - Tapa posterior con cuatro tornillos M3

Cómo ejecutar:
  Fusion 360 → Utilidades → Scripts y complementos → Scripts → Ejecutar
"""

import adsk.core
import adsk.fusion
import traceback

# ─── Parámetros editables ─────────────────────────────────────────────────────
CAJA_W     = 160    # mm — ancho interno de la caja
CAJA_D     = 100    # mm — profundidad de la caja
CAJA_H     = 60     # mm — alto de la caja
PARED      = 3      # mm — espesor de paredes
TORNILLO_D = 3.2    # mm — diámetro pase tornillo M3
MARGEN_T   = 8      # mm — margen desde esquinas para tornillos


def _rect_sketch(sketch, x0, y0, w, h):
    """Dibuja un rectángulo en el sketch dado."""
    ls = sketch.sketchCurves.sketchLines
    p0 = adsk.core.Point3D.create(x0,     y0,     0)
    p1 = adsk.core.Point3D.create(x0 + w, y0,     0)
    p2 = adsk.core.Point3D.create(x0 + w, y0 + h, 0)
    p3 = adsk.core.Point3D.create(x0,     y0 + h, 0)
    ls.addByTwoPoints(p0, p1)
    ls.addByTwoPoints(p1, p2)
    ls.addByTwoPoints(p2, p3)
    ls.addByTwoPoints(p3, p0)


def _circulo(sketch, cx, cy, diam):
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

        ext_w = CAJA_W + 2 * PARED
        ext_d = CAJA_D + 2 * PARED

        # ── 1. Cuerpo exterior de la caja ────────────────────────────────────
        sk_ext = sketches.add(xy_plane)
        _rect_sketch(sk_ext, 0, 0, ext_w, ext_d)
        _rect_sketch(sk_ext, PARED, PARED, CAJA_W, CAJA_D)

        # Tomar el perfil de la cáscara (el más grande con hueco interior)
        prof_caja = None
        for i in range(sk_ext.profiles.count):
            p  = sk_ext.profiles.item(i)
            bb = p.boundingBox
            pw = abs(bb.maxPoint.x - bb.minPoint.x)
            ph = abs(bb.maxPoint.y - bb.minPoint.y)
            if pw > ext_w * 0.9 and ph > ext_d * 0.9:
                prof_caja = p
                break
        if prof_caja is None:
            prof_caja = sk_ext.profiles.item(0)

        ext_in = extrudes.createInput(
            prof_caja,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_in.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(CAJA_H / 10)
        )
        ext_caja = extrudes.add(ext_in)
        ext_caja.bodies.item(0).name = "Caja_Electronica"

        # ── 2. Tapa posterior con huecos de tornillo ─────────────────────────
        sk_tapa = sketches.add(xy_plane)
        _rect_sketch(sk_tapa, 0, 0, ext_w, ext_d)

        # Cuatro tornillos en las esquinas
        tornillos = [
            (MARGEN_T,           MARGEN_T),
            (ext_w - MARGEN_T,   MARGEN_T),
            (ext_w - MARGEN_T,   ext_d - MARGEN_T),
            (MARGEN_T,           ext_d - MARGEN_T),
        ]
        for tx, ty in tornillos:
            _circulo(sk_tapa, tx, ty, TORNILLO_D)

        # Seleccionar perfil exterior de la tapa (sin tornillos)
        prof_tapa = None
        for i in range(sk_tapa.profiles.count):
            p  = sk_tapa.profiles.item(i)
            bb = p.boundingBox
            pw = abs(bb.maxPoint.x - bb.minPoint.x)
            ph = abs(bb.maxPoint.y - bb.minPoint.y)
            if pw > ext_w * 0.9 and ph > ext_d * 0.9:
                prof_tapa = p
                break
        if prof_tapa is None:
            prof_tapa = sk_tapa.profiles.item(0)

        # Offset en Z para colocar la tapa debajo (-PARED)
        offset_plane = root.constructionPlanes
        offset_input = offset_plane.createInput()
        offset_input.setByOffset(
            xy_plane,
            adsk.core.ValueInput.createByReal(-PARED / 10)
        )
        tapa_plane = offset_plane.add(offset_input)

        sk_tapa2 = sketches.add(tapa_plane)
        _rect_sketch(sk_tapa2, 0, 0, ext_w, ext_d)
        for tx, ty in tornillos:
            _circulo(sk_tapa2, tx, ty, TORNILLO_D)

        prof_tapa2 = None
        for i in range(sk_tapa2.profiles.count):
            p  = sk_tapa2.profiles.item(i)
            bb = p.boundingBox
            pw = abs(bb.maxPoint.x - bb.minPoint.x)
            ph = abs(bb.maxPoint.y - bb.minPoint.y)
            if pw > ext_w * 0.9 and ph > ext_d * 0.9:
                prof_tapa2 = p
                break
        if prof_tapa2 is None:
            prof_tapa2 = sk_tapa2.profiles.item(0)

        ext_tapa_in = extrudes.createInput(
            prof_tapa2,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_tapa_in.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(PARED / 10)
        )
        ext_tapa = extrudes.add(ext_tapa_in)
        ext_tapa.bodies.item(0).name = "Tapa_Posterior"

        ui.messageBox(
            "✅ Caja electrónica generada:\n"
            "  • Interior: {}×{}×{} mm\n"
            "  • Pared: {} mm\n"
            "  • Tornillos M3 en 4 esquinas".format(
                CAJA_W, CAJA_D, CAJA_H, PARED
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Error:\n{}".format(traceback.format_exc()))
