# ruff: noqa: E402, I001
import sys
from pathlib import Path

import bpy

ROOT = str(Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from quality_actions import upgrade as upgrade_actions
from quality_cube import cube, upgrade_nader_face
from quality_environment import upgrade as upgrade_environment
from quality_meshes import sphere, upgrade_omar_face
from quality_torus import torus, upgrade_omar_glasses
from quality_weather import upgrade as upgrade_weather


def main():
    upgrade_environment()
    upgrade_omar_face(cube)
    upgrade_nader_face(sphere, torus)
    upgrade_omar_glasses(cube)
    upgrade_actions()
    upgrade_weather(cube)
    path = bpy.data.filepath
    if not path:
        raise RuntimeError("Quality upgrade requires an opened .blend file")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("BLENDER_QUALITY_UPGRADE_SUCCEEDED=" + path)


if __name__ == "__main__":
    main()
