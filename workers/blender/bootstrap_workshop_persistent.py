import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("bootstrap_workshop.py")
MODULE_SPEC = importlib.util.spec_from_file_location("bootstrap_workshop", MODULE_PATH)

if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise RuntimeError(f"Unable to load Blender bootstrap module: {MODULE_PATH}")

bootstrap_workshop = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = bootstrap_workshop
MODULE_SPEC.loader.exec_module(bootstrap_workshop)


def _create_persistent_action(name, rig, action_name, keys):
    action = bootstrap_workshop.bpy.data.actions.new(f"{name}_{action_name}")
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action

    for frame, bone_name, rotation in keys:
        bootstrap_workshop._keyframe_bone(rig, bone_name, frame, rotation)

    rig.animation_data.action = None

    track = rig.animation_data.nla_tracks.new()
    track.name = f"LIB_{action.name}"
    track.mute = True
    strip = track.strips.new(action.name, 1, action)
    strip.name = action.name


bootstrap_workshop._create_action = _create_persistent_action


if __name__ == "__main__":
    bootstrap_workshop.main()
