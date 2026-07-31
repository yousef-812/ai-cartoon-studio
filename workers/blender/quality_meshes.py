import bpy

from quality_common import apply_material, material, parent_to_bone, smooth


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


def upgrade_omar_face(cube):
    rig = bpy.data.objects["Omar_Rig"]
    head = bpy.data.objects["Omar_Head"]
    skin = material("Q_SkinOmar", (0.50, 0.27, 0.16, 1), 0.58)
    white = material("Q_EyeWhite", (0.94, 0.96, 0.98, 1), 0.30)
    iris = material("Q_BrownIris", (0.20, 0.07, 0.02, 1), 0.25)
    dark = material("Q_Dark", (0.008, 0.012, 0.018, 1), 0.40)
    head.scale = (1.10, 1.05, 1.08)
    smooth(head)
    apply_material(head, skin)
    for suffix, x in (("L", 0.115), ("R", -0.115)):
        eye = bpy.data.objects.get(f"Omar_Eye_{suffix}")
        if eye is not None:
            eye.scale = (1.45, 1.0, 1.30)
            apply_material(eye, white)
            smooth(eye)
        parts = (
            sphere(f"Omar_Iris_{suffix}", (x, -0.302, 2.04), (0.039, 0.017, 0.043), iris),
            sphere(f"Omar_Pupil_{suffix}", (x, -0.320, 2.04), (0.017, 0.009, 0.024), dark),
            cube(f"Omar_Brow_{suffix}", (x, -0.322, 2.145), (0.083, 0.011, 0.015), dark, (0, -8 if suffix == "L" else 8, 0), 0.012),
            cube(f"Omar_Eyelid_{suffix}", (x, -0.326, 2.092), (0.074, 0.010, 0.012), skin, width=0.010),
        )
        for part in parts:
            parent_to_bone(part, rig, "head")
    for part in (
        sphere("Omar_Nose", (0, -0.315, 1.965), (0.050, 0.050, 0.065), skin),
        sphere("Omar_Ear_L", (0.31, -0.005, 1.99), (0.055, 0.040, 0.073), skin),
        sphere("Omar_Ear_R", (-0.31, -0.005, 1.99), (0.055, 0.040, 0.073), skin),
        sphere("Omar_HairLock", (0.17, -0.01, 2.23), (0.16, 0.13, 0.10), dark),
    ):
        parent_to_bone(part, rig, "head")
