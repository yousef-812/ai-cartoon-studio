import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _arguments() -> argparse.Namespace:
    separator = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(sys.argv[separator + 1 :])


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.armatures,
        bpy.data.actions,
    ):
        for item in list(collection):
            collection.remove(item)


def _material(name: str, color: tuple[float, float, float, float], metallic: float = 0.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = 0.55
        principled.inputs["Metallic"].default_value = metallic
    return material


def _apply_material(obj, material) -> None:
    if obj.data is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)


def _bevel(obj, amount: float = 0.08) -> None:
    modifier = obj.modifiers.new(name="Soft edges", type="BEVEL")
    modifier.width = amount
    modifier.segments = 3


def _cube(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material,
):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _bevel(obj)
    _apply_material(obj, material)
    return obj


def _sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material,
):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _apply_material(obj, material)
    return obj


def _cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material,
):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    _bevel(obj, 0.04)
    _apply_material(obj, material)
    return obj


def _empty(name: str, location: tuple[float, float, float]):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.35
    bpy.context.collection.objects.link(obj)
    return obj


def _look_at(obj, target: tuple[float, float, float], track: str = "-Z", up: str = "Y") -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat(track, up).to_euler()


def _camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], lens: int):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    _look_at(obj, target)
    return obj


def _light(
    name: str,
    light_type: str,
    location: tuple[float, float, float],
    energy: float,
    color: tuple[float, float, float],
    size: float = 3.0,
):
    data = bpy.data.lights.new(name=name, type=light_type)
    data.energy = energy
    data.color = color
    if hasattr(data, "shape"):
        data.shape = "DISK"
    if hasattr(data, "size"):
        data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def _parent_to_bone(obj, rig, bone_name: str) -> None:
    matrix_world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = matrix_world


def _create_armature(name: str):
    data = bpy.data.armatures.new(f"{name}_Armature")
    rig = bpy.data.objects.new(f"{name}_Rig", data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    definitions = {
        "root": ((0, 0, 0), (0, 0, 0.25), None),
        "spine": ((0, 0, 0.85), (0, 0, 1.55), "root"),
        "neck": ((0, 0, 1.55), (0, 0, 1.78), "spine"),
        "head": ((0, 0, 1.78), (0, 0, 2.18), "neck"),
        "upper_arm.L": ((0, 0, 1.45), (0.55, 0, 1.40), "spine"),
        "forearm.L": ((0.55, 0, 1.40), (0.95, 0, 1.10), "upper_arm.L"),
        "hand.L": ((0.95, 0, 1.10), (1.12, 0, 1.02), "forearm.L"),
        "upper_arm.R": ((0, 0, 1.45), (-0.55, 0, 1.40), "spine"),
        "forearm.R": ((-0.55, 0, 1.40), (-0.95, 0, 1.10), "upper_arm.R"),
        "hand.R": ((-0.95, 0, 1.10), (-1.12, 0, 1.02), "forearm.R"),
        "thigh.L": ((0.22, 0, 0.85), (0.22, 0, 0.35), "root"),
        "shin.L": ((0.22, 0, 0.35), (0.22, 0, -0.15), "thigh.L"),
        "foot.L": ((0.22, 0, -0.15), (0.22, -0.28, -0.18), "shin.L"),
        "thigh.R": ((-0.22, 0, 0.85), (-0.22, 0, 0.35), "root"),
        "shin.R": ((-0.22, 0, 0.35), (-0.22, 0, -0.15), "thigh.R"),
        "foot.R": ((-0.22, 0, -0.15), (-0.22, -0.28, -0.18), "shin.R"),
    }
    for bone_name, (head, tail, parent_name) in definitions.items():
        bone = data.edit_bones.new(bone_name)
        bone.head = head
        bone.tail = tail
        if parent_name:
            bone.parent = data.edit_bones[parent_name]
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)
    return rig


def _create_character(
    name: str,
    *,
    skin,
    jacket,
    shirt,
    trousers,
    hair,
    accent,
    scale: float,
):
    rig = _create_armature(name)
    rig.scale = (scale, scale, scale)

    torso = _cube(f"{name}_Torso", (0, 0, 1.22), (0.42, 0.23, 0.44), jacket)
    chest = _cube(f"{name}_Shirt", (0, -0.245, 1.24), (0.23, 0.02, 0.31), shirt)
    neck = _cylinder(f"{name}_Neck", (0, 0, 1.67), 0.12, 0.2, skin)
    head = _sphere(f"{name}_Head", (0, -0.02, 1.98), (0.30, 0.27, 0.36), skin)
    hair_obj = _sphere(f"{name}_Hair", (0, 0.02, 2.24), (0.31, 0.26, 0.15), hair)
    mouth = _cube(f"{name}_Mouth", (0, -0.285, 1.90), (0.10, 0.018, 0.035), accent)
    left_eye = _sphere(f"{name}_Eye_L", (0.11, -0.272, 2.04), (0.055, 0.025, 0.045), accent)
    right_eye = _sphere(f"{name}_Eye_R", (-0.11, -0.272, 2.04), (0.055, 0.025, 0.045), accent)

    for obj in (torso, chest):
        _parent_to_bone(obj, rig, "spine")
    for obj in (neck,):
        _parent_to_bone(obj, rig, "neck")
    for obj in (head, hair_obj, mouth, left_eye, right_eye):
        _parent_to_bone(obj, rig, "head")

    limb_specs = (
        ("UpperArm_L", (0.30, 0, 1.40), (0.26, 0.15, 0.16), jacket, "upper_arm.L"),
        ("Forearm_L", (0.72, 0, 1.23), (0.22, 0.13, 0.15), skin, "forearm.L"),
        ("Hand_L", (1.02, -0.01, 1.05), (0.12, 0.09, 0.14), skin, "hand.L"),
        ("UpperArm_R", (-0.30, 0, 1.40), (0.26, 0.15, 0.16), jacket, "upper_arm.R"),
        ("Forearm_R", (-0.72, 0, 1.23), (0.22, 0.13, 0.15), skin, "forearm.R"),
        ("Hand_R", (-1.02, -0.01, 1.05), (0.12, 0.09, 0.14), skin, "hand.R"),
        ("Thigh_L", (0.22, 0, 0.62), (0.18, 0.18, 0.28), trousers, "thigh.L"),
        ("Shin_L", (0.22, 0, 0.10), (0.16, 0.17, 0.28), trousers, "shin.L"),
        ("Foot_L", (0.22, -0.13, -0.18), (0.17, 0.28, 0.10), accent, "foot.L"),
        ("Thigh_R", (-0.22, 0, 0.62), (0.18, 0.18, 0.28), trousers, "thigh.R"),
        ("Shin_R", (-0.22, 0, 0.10), (0.16, 0.17, 0.28), trousers, "shin.R"),
        ("Foot_R", (-0.22, -0.13, -0.18), (0.17, 0.28, 0.10), accent, "foot.R"),
    )
    for part_name, location, part_scale, material, bone_name in limb_specs:
        part = _cube(f"{name}_{part_name}", location, part_scale, material)
        _parent_to_bone(part, rig, bone_name)

    _create_actions(name, rig)
    return rig


def _keyframe_bone(rig, bone_name: str, frame: int, rotation: tuple[float, float, float]) -> None:
    bone = rig.pose.bones[bone_name]
    bone.rotation_euler = tuple(math.radians(value) for value in rotation)
    bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)


def _create_action(name: str, rig, action_name: str, keys: list[tuple[int, str, tuple[float, float, float]]]):
    action = bpy.data.actions.new(f"{name}_{action_name}")
    rig.animation_data_create()
    rig.animation_data.action = action
    for frame, bone_name, rotation in keys:
        _keyframe_bone(rig, bone_name, frame, rotation)
    rig.animation_data.action = None


def _create_actions(name: str, rig) -> None:
    _create_action(
        name,
        rig,
        "Idle",
        [
            (1, "spine", (0, 0, -1.5)),
            (24, "spine", (0, 0, 1.5)),
            (48, "spine", (0, 0, -1.5)),
        ],
    )
    _create_action(
        name,
        rig,
        "Talk",
        [
            (1, "upper_arm.L", (5, 0, -8)),
            (12, "upper_arm.L", (-12, 0, 18)),
            (24, "upper_arm.L", (6, 0, -10)),
            (36, "upper_arm.R", (-10, 0, -18)),
            (48, "upper_arm.R", (5, 0, 8)),
            (1, "head", (0, 0, -2)),
            (24, "head", (3, 0, 2)),
            (48, "head", (0, 0, -2)),
        ],
    )
    _create_action(
        name,
        rig,
        "Listen",
        [
            (1, "head", (0, 0, 5)),
            (24, "head", (3, 0, 9)),
            (48, "head", (0, 0, 5)),
        ],
    )
    _create_action(
        name,
        rig,
        "Point",
        [
            (1, "upper_arm.L", (0, 0, 0)),
            (18, "upper_arm.L", (0, -45, -55)),
            (18, "forearm.L", (0, -15, -30)),
            (48, "upper_arm.L", (0, -45, -55)),
        ],
    )
    _create_action(
        name,
        rig,
        "PickUp",
        [
            (1, "upper_arm.L", (0, 0, 0)),
            (18, "upper_arm.L", (25, 0, -20)),
            (18, "forearm.L", (45, 0, -15)),
            (36, "upper_arm.L", (-20, 0, 10)),
            (36, "forearm.L", (-50, 0, 10)),
        ],
    )
    for action_name in ("Walk", "Surprised", "Worried"):
        _create_action(name, rig, action_name, [(1, "spine", (0, 0, 0)), (48, "spine", (0, 0, 0))])


def _build_workshop() -> None:
    cream = _material("Cream", (0.78, 0.71, 0.58, 1))
    dark_wood = _material("DarkWood", (0.20, 0.10, 0.05, 1))
    wood = _material("Wood", (0.42, 0.22, 0.10, 1))
    teal = _material("Teal", (0.02, 0.43, 0.48, 1))
    orange = _material("Orange", (0.85, 0.28, 0.06, 1))
    navy = _material("Navy", (0.03, 0.08, 0.22, 1))
    charcoal = _material("Charcoal", (0.08, 0.09, 0.11, 1))
    skin_omar = _material("SkinOmar", (0.48, 0.25, 0.14, 1))
    skin_nader = _material("SkinNader", (0.58, 0.38, 0.21, 1))
    black = _material("Black", (0.015, 0.02, 0.025, 1))
    lantern_cream = _material("LanternCream", (0.92, 0.84, 0.62, 1))
    brass = _material("Brass", (0.65, 0.36, 0.08, 1), metallic=0.6)

    _cube("ENV_Floor", (0, 0, -0.35), (5.5, 4.5, 0.15), dark_wood)
    _cube("ENV_BackWall", (0, 4.25, 2.3), (5.5, 0.15, 2.65), cream)
    _cube("ENV_LeftWall", (-5.35, 0, 2.3), (0.15, 4.3, 2.65), cream)
    _cube("ENV_RightWall", (5.35, 0, 2.3), (0.15, 4.3, 2.65), cream)

    _cube("ENV_WorkbenchTop", (0, 0.85, 1.05), (2.7, 0.65, 0.12), wood)
    for x in (-2.35, 2.35):
        _cube(f"ENV_WorkbenchLeg_{x}", (x, 0.85, 0.25), (0.14, 0.5, 0.7), dark_wood)
    _cube("ENV_Shelf", (3.8, 2.7, 2.0), (1.0, 0.35, 0.08), wood)
    _cube("ENV_Toolboard", (-3.8, 3.9, 2.0), (1.0, 0.08, 1.2), teal)

    _cube("ENV_WindowFrame", (-1.9, 4.05, 2.6), (1.25, 0.08, 1.0), dark_wood)
    _cube("ENV_WindowGlass", (-1.9, 3.95, 2.6), (1.08, 0.03, 0.83), navy)
    for x in (-1.9,):
        _cube("ENV_WindowBarV", (x, 3.86, 2.6), (0.04, 0.03, 0.83), cream)
    _cube("ENV_WindowBarH", (-1.9, 3.86, 2.6), (1.08, 0.03, 0.04), cream)

    lantern = _cylinder("PROP_Lantern", (0.7, 0.72, 1.35), 0.20, 0.42, lantern_cream)
    handle = _cube("PROP_Lantern_Handle", (0.7, 0.72, 1.68), (0.22, 0.04, 0.05), teal)
    handle.parent = lantern
    _cube("PROP_Screwdriver", (-0.8, 0.65, 1.25), (0.28, 0.04, 0.04), brass)

    _empty("ANCHOR_Workbench_Center", (0, -0.25, 0))
    _empty("ANCHOR_Omar_Left", (-1.45, -0.35, 0))
    _empty("ANCHOR_Omar_Center", (-0.45, -0.35, 0))
    _empty("ANCHOR_Nader_Right", (1.45, -0.35, 0))
    _empty("ANCHOR_Nader_Center", (0.45, -0.35, 0))

    _create_character(
        "Omar",
        skin=skin_omar,
        jacket=teal,
        shirt=lantern_cream,
        trousers=charcoal,
        hair=black,
        accent=black,
        scale=1.0,
    )
    _create_character(
        "Nader",
        skin=skin_nader,
        jacket=navy,
        shirt=orange,
        trousers=charcoal,
        hair=black,
        accent=black,
        scale=0.94,
    )

    wide = _camera("CAM_Wide", (0, -9.2, 3.4), (0, 0.4, 1.25), 48)
    _camera("CAM_Medium", (0, -6.2, 2.7), (0, 0.0, 1.45), 58)
    _camera("CAM_Close", (-1.2, -4.3, 2.25), (-1.2, -0.25, 1.75), 72)
    bpy.context.scene.camera = wide

    key = _light("LIGHT_Key", "AREA", (-3.5, -3.0, 5.5), 1050, (1.0, 0.72, 0.48), 4.0)
    _look_at(key, (0, 0, 1.2))
    fill = _light("LIGHT_Fill", "AREA", (3.5, -1.5, 3.8), 650, (0.45, 0.65, 1.0), 3.0)
    _look_at(fill, (0, 0, 1.4))
    _light("LIGHT_Lantern", "POINT", (0.7, 0.45, 1.45), 260, (1.0, 0.48, 0.16), 1.0)

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.world.color = (0.025, 0.018, 0.015)


def main() -> None:
    args = _arguments()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    _clear_scene()
    _build_workshop()
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f"BLENDER_WORKSHOP_READY={output}")


if __name__ == "__main__":
    main()
