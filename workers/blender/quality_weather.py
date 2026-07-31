# ruff: noqa: I001
import bpy

from quality_common import ensure_anchor, material


def _animate_rain(drop, base_z, offset):
    start = 1 + offset
    end = 20 + offset
    drop.location.z = base_z + 0.45
    drop.keyframe_insert(data_path="location", frame=start, index=2)
    drop.location.z = base_z - 0.75
    drop.keyframe_insert(data_path="location", frame=end, index=2)
    if drop.animation_data and drop.animation_data.action:
        for curve in drop.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
            curve.modifiers.new("CYCLES")


def upgrade(cube):
    ensure_anchor("ANCHOR_Window_Focus", (-1.9, 3.75, 2.55))
    ensure_anchor("ANCHOR_Lantern_Focus", (0.7, 0.72, 1.45))
    rain = material("Q_Rain", (0.55, 0.72, 1.0, 1), 0.20)
    for index, x in enumerate((-2.65, -2.35, -2.05, -1.75, -1.45, -1.15)):
        base_z = 2.15 + ((index % 3) * 0.35)
        drop = cube(
            f"FX_RainDrop_{index}",
            (x, 3.80, base_z),
            (0.010, 0.010, 0.15),
            rain,
            width=0.004,
        )
        drop.hide_render = False
        drop.hide_viewport = False
        _animate_rain(drop, base_z, index * 3)
    key = bpy.data.objects.get("LIGHT_Key")
    fill = bpy.data.objects.get("LIGHT_Fill")
    lantern = bpy.data.objects.get("LIGHT_Lantern")
    if key and key.data:
        key.data.energy = 760
        key.data.color = (0.72, 0.82, 1.0)
    if fill and fill.data:
        fill.data.energy = 420
        fill.data.color = (0.32, 0.48, 0.82)
    if lantern and lantern.data:
        lantern.data.energy = 220
        lantern.data.color = (1.0, 0.34, 0.07)
    scene = bpy.context.scene
    scene.world.color = (0.008, 0.014, 0.028)
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
