import math

import bpy

from quality_common import apply_material, bevel


def cube(name, location, scale, value, rotation=(0, 0, 0), width=0.03):
    obj = bpy.data.objects.get(name)
    if obj is None:
        bpy.ops.mesh.primitive_cube_add(location=location)
        obj = bpy.context.object
        obj.name = name
    obj.location = location
    obj.rotation_euler = tuple(math.radians(v) for v in rotation)
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)
    bevel(obj, width)
    apply_material(obj, value)
    return obj
