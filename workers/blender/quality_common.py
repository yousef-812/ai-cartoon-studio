import math
import sys
from pathlib import Path

import bpy


def material(name, color, roughness=0.5, metallic=0.0):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = color
    value.use_nodes = True
    node = value.node_tree.nodes.get("Principled BSDF")
    if node is not None:
        node.inputs["Base Color"].default_value = color
        node.inputs["Roughness"].default_value = roughness
        node.inputs["Metallic"].default_value = metallic
    return value


def apply_material(obj, value):
    if obj.data is not None and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(value)


def smooth(obj):
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def bevel(obj, width):
    modifier = obj.modifiers.get("QualityBevel") or obj.modifiers.new("QualityBevel", "BEVEL")
    modifier.width = width
    modifier.segments = 3


def parent_to_bone(obj, rig, bone):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def ensure_anchor(name, location):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def set_material(name, value):
    obj = bpy.data.objects.get(name)
    if obj is not None:
        apply_material(obj, value)


def set_scale(name, scale, width=0.0):
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.scale = scale
    if width and obj.type == "MESH":
        bevel(obj, width)


def module_path():
    path = str(Path(__file__).resolve().parent)
    if path not in sys.path:
        sys.path.insert(0, path)
