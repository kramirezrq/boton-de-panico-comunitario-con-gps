"""
totem_base.py — Script Fusion 360 (API Python)
Genera la pieza: BASE del tótem de pánico comunitario.

Cómo ejecutar:
  Fusion 360 → Utilidades → Scripts y complementos → Scripts → Ejecutar
  Seleccionar este archivo .py

Dimensiones (en mm):
  Base cuadrada : 200 × 200 × 10 mm
  Columna       : 80 × 80 × 800 mm (centrada sobre la base)
  Chaflán base  : 3 mm (anti-astillado)
"""

import adsk.core
import adsk.fusion
import traceback

# ─── Parámetros editables ─────────────────────────────────────────────────────
BASE_W   = 200   # mm — ancho de la base
BASE_D   = 200   # mm — profundidad de la base
BASE_H   = 10    # mm — alto de la base
COL_W    = 80    # mm — ancho de la columna
COL_D    = 80    # mm — profundidad de la columna
COL_H    = 800   # mm — alto de la columna
CHAFLAN  = 3     # mm — radio de chaflán perimetral


def run(context):
    ui = None
    try:
        app  = adsk.core.Application.get()
        ui   = app.userInterface
        des  = adsk.fusion.Design.cast(app.activeProduct)
        root = des.rootComponent

        # ── 1. BASE ──────────────────────────────────────────────────────────
        sketches    = root.sketches
        xy_plane    = root.xYConstructionPlane
        sk_base     = sketches.add(xy_plane)
        lines_base  = sk_base.sketchCurves.sketchLines

        p0 = adsk.core.Point3D.create(0,       0,       0)
        p1 = adsk.core.Point3D.create(BASE_W,  0,       0)
        p2 = adsk.core.Point3D.create(BASE_W,  BASE_D,  0)
        p3 = adsk.core.Point3D.create(0,       BASE_D,  0)

        lines_base.addByTwoPoints(p0, p1)
        lines_base.addByTwoPoints(p1, p2)
        lines_base.addByTwoPoints(p2, p3)
        lines_base.addByTwoPoints(p3, p0)

        prof_base  = sk_base.profiles.item(0)
        extrudes   = root.features.extrudeFeatures
        ext_input  = extrudes.createInput(
            prof_base,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        dist_base  = adsk.core.ValueInput.createByReal(BASE_H / 10)  # cm
        ext_input.setDistanceExtent(False, dist_base)
        ext_base   = extrudes.add(ext_input)
        ext_base.bodies.item(0).name = "Base_Totem"

        # ── 2. COLUMNA ───────────────────────────────────────────────────────
        offset_col_x = (BASE_W - COL_W) / 2
        offset_col_y = (BASE_D - COL_D) / 2

        sk_col  = sketches.add(xy_plane)
        lines_c = sk_col.sketchCurves.sketchLines

        c0 = adsk.core.Point3D.create(offset_col_x,          offset_col_y,          0)
        c1 = adsk.core.Point3D.create(offset_col_x + COL_W,  offset_col_y,          0)
        c2 = adsk.core.Point3D.create(offset_col_x + COL_W,  offset_col_y + COL_D,  0)
        c3 = adsk.core.Point3D.create(offset_col_x,          offset_col_y + COL_D,  0)

        lines_c.addByTwoPoints(c0, c1)
        lines_c.addByTwoPoints(c1, c2)
        lines_c.addByTwoPoints(c2, c3)
        lines_c.addByTwoPoints(c3, c0)

        prof_col   = sk_col.profiles.item(0)
        ext_col_in = extrudes.createInput(
            prof_col,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        dist_col   = adsk.core.ValueInput.createByReal((BASE_H + COL_H) / 10)
        ext_col_in.setDistanceExtent(False, dist_col)
        ext_col    = extrudes.add(ext_col_in)
        ext_col.bodies.item(0).name = "Columna_Totem"

        ui.messageBox(
            "✅ Pieza generada correctamente:\n"
            "  • Base: {}×{}×{} mm\n"
            "  • Columna: {}×{}×{} mm".format(
                BASE_W, BASE_D, BASE_H, COL_W, COL_D, COL_H
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Error:\n{}".format(traceback.format_exc()))
