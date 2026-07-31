# ruff: noqa: I001
import math

import bpy

from quality_common import apply_material, material, parent_to_bone, smooth


def torus(name, location, major_radius, minor_radius, value):
    obj = bpy.data.objects.get(name)
    if obj is None:
        bpy.ops.mesh.primitive_torus_add(
            major_radius=major_radius,
            minor_radius=minor_radius,
            major_segments=36,
            minor_segments=10,
            location=location,
            rotation=(math.radians(90), 0, 0),
        )
        obj = bpy.context.object
        obj.name = name
    obj.location = location
    smooth(obj)
    apply_material(obj, value)
    return obj


def upgrade_omar_glasses(cube):
    rig = bpy.data.objects["Omar_Rig"]
    frames = material("Q_Glasses", (0.02, 0.03, 0.04, 1), 0.20, 0.35)
    for suffix, x in (("L", 0.115), ("R", -0.115)):
        frame = torus(f"Omar_Glasses_{suffix}", (x, -0.347, 2.04), 0.092, 0.010, frames)
        parent_to_bone(frame, rig, "head")
    bridge = cube("Omar_Glasses_Bridge", (0, -0.347, 2.04), (0.030, 0.009, 0.009), frames, width=0.006)
    parent_to_bone(bridge, rig, "head")
