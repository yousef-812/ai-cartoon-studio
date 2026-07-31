import math

import bpy


def _key(rig, bone, frame, rotation):
    pose = rig.pose.bones[bone]
    pose.rotation_mode = "XYZ"
    pose.rotation_euler = tuple(math.radians(v) for v in rotation)
    pose.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone)


def _action(name, rig, keys):
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    for frame, bone, rotation in keys:
        _key(rig, bone, frame, rotation)
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
    rig.animation_data.action = None


def upgrade():
    for name in ("Omar", "Nader"):
        rig = bpy.data.objects[f"{name}_Rig"]
        _action(f"{name}_Surprised", rig, [(1, "spine", (0, 0, 0)), (6, "spine", (-12, 0, 0)), (7, "head", (-9, 0, 0)), (8, "upper_arm.L", (-28, -10, 32)), (8, "upper_arm.R", (-28, 10, -32)), (34, "spine", (-2, 0, 0)), (48, "spine", (1, 0, 0))])
        _action(f"{name}_Worried", rig, [(1, "spine", (3, 0, 0)), (12, "spine", (7, 0, 0)), (18, "head", (6, 0, 2)), (24, "upper_arm.L", (11, 0, 8)), (24, "upper_arm.R", (9, 0, -8)), (48, "spine", (4, 0, 0))])
        _action(f"{name}_ReactLightOut", rig, [(1, "spine", (0, 0, 0)), (5, "spine", (-13, 0, 0)), (5, "head", (-10, 0, 0)), (7, "upper_arm.L", (-32, -12, 35)), (7, "upper_arm.R", (-32, 12, -35)), (24, "head", (4, 0, 0)), (48, "spine", (3, 0, 0))])
        _action(f"{name}_ConcernSettle", rig, [(1, "spine", (4, 0, 0)), (1, "head", (3, 0, 0)), (16, "head", (6, 0, 2)), (28, "upper_arm.L", (9, 0, 6)), (28, "upper_arm.R", (8, 0, -6)), (48, "spine", (3, 0, 0))])
