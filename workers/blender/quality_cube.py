import math

import bpy

from quality_common import apply_material, bevel, material, parent_to_bone, smooth


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


def upgrade_nader_face(sphere, torus):
    rig = bpy.data.objects["Nader_Rig"]
    head = bpy.data.objects["Nader_Head"]
    skin = material("Q_SkinNader", (0.62, 0.40, 0.23, 1), 0.58)
    white = material("Q_EyeWhite", (0.94, 0.96, 0.98, 1), 0.30)
    iris = material("Q_BlueIris", (0.03, 0.20, 0.34, 1), 0.25)
    dark = material("Q_Dark", (0.008, 0.012, 0.018, 1), 0.40)
    navy = material("Q_Navy", (0.018, 0.045, 0.13, 1), 0.52)
    head.scale = (1.12, 1.06, 1.10)
    smooth(head)
    apply_material(head, skin)
    for suffix, x in (("L", 0.125), ("R", -0.125)):
        eye = bpy.data.objects.get(f"Nader_Eye_{suffix}")
        if eye is not None:
            eye.scale = (1.55, 1.0, 1.42)
            apply_material(eye, white)
            smooth(eye)
        parts = (
            sphere(f"Nader_Iris_{suffix}", (x, -0.302, 2.04), (0.043, 0.018, 0.047), iris),
            sphere(f"Nader_Pupil_{suffix}", (x, -0.320, 2.04), (0.018, 0.009, 0.025), dark),
            cube(f"Nader_Brow_{suffix}", (x, -0.322, 2.148), (0.088, 0.011, 0.016), navy, (0, -6 if suffix == "L" else 6, 0), 0.012),
            cube(f"Nader_Eyelid_{suffix}", (x, -0.326, 2.095), (0.078, 0.010, 0.012), skin, width=0.010),
        )
        for part in parts:
            parent_to_bone(part, rig, "head")
    for part in (
        sphere("Nader_Nose", (0, -0.315, 1.965), (0.047, 0.048, 0.061), skin),
        sphere("Nader_Ear_L", (0.31, -0.005, 1.99), (0.053, 0.039, 0.070), skin),
        sphere("Nader_Ear_R", (-0.31, -0.005, 1.99), (0.053, 0.039, 0.070), skin),
    ):
        parent_to_bone(part, rig, "head")
    hood = torus("Nader_Hood", (0, 0.025, 1.99), 0.325, 0.045, navy)
    hood.scale.z = 1.12
    parent_to_bone(hood, rig, "head")
