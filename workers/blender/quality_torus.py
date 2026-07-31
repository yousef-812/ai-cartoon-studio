import math

import bpy

from quality_common import apply_material, smooth


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
