import bpy

from quality_common import apply_material, smooth


def sphere(name, location, scale, value):
    obj = bpy.data.objects.get(name)
    if obj is None:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
        obj = bpy.context.object
        obj.name = name
    obj.location = location
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)
    smooth(obj)
    apply_material(obj, value)
    return obj
