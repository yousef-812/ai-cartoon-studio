import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

_CAMERA_FOCUS_HEIGHTS = {
    "wide": 1.35,
    "medium": 1.55,
    "close": 1.90,
}
_CLOSE_CAMERA_SIDE_OFFSET = 0.55


def _arguments() -> argparse.Namespace:
    separator = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(sys.argv[separator + 1 :])


def _object(name: str, *, required: bool = True):
    value = bpy.data.objects.get(name)
    if value is None and required:
        raise RuntimeError(f"Required Blender object is missing: {name}")
    return value


def _descendants(obj):
    for child in obj.children:
        yield child
        yield from _descendants(child)


def _set_character_visibility(rig, visible: bool) -> None:
    for obj in (rig, *_descendants(rig)):
        obj.hide_render = not visible
        obj.hide_viewport = not visible


def _prepare_character_visibility(character_cues: list[dict[str, object]]) -> None:
    active_rigs = {str(cue.get("rig_object", "")) for cue in character_cues}
    scene_rigs = [
        obj
        for obj in bpy.data.objects
        if obj.type == "ARMATURE" and obj.name.endswith("_Rig")
    ]
    for rig in scene_rigs:
        _set_character_visibility(rig, rig.name in active_rigs)
    print(f"VISIBLE_CHARACTERS={','.join(sorted(active_rigs))}")


def _set_transform(obj, transform: dict[str, object]) -> None:
    location = transform.get("location", {})
    rotation = transform.get("rotation_degrees", {})
    scale = transform.get("scale", {})
    obj.location = (
        float(location.get("x", 0)),
        float(location.get("y", 0)),
        float(location.get("z", 0)),
    )
    obj.rotation_euler = tuple(
        math.radians(float(rotation.get(axis, 0))) for axis in ("x", "y", "z")
    )
    obj.scale = tuple(float(scale.get(axis, 1)) for axis in ("x", "y", "z"))


def _copy_anchor_transform(rig, anchor, offset: dict[str, object]) -> None:
    rig.matrix_world = anchor.matrix_world.copy()
    location = offset.get("location", {})
    rotation = offset.get("rotation_degrees", {})
    scale = offset.get("scale", {})
    rig.location += Vector(
        (
            float(location.get("x", 0)),
            float(location.get("y", 0)),
            float(location.get("z", 0)),
        )
    )
    rig.rotation_euler.rotate_axis("X", math.radians(float(rotation.get("x", 0))))
    rig.rotation_euler.rotate_axis("Y", math.radians(float(rotation.get("y", 0))))
    rig.rotation_euler.rotate_axis("Z", math.radians(float(rotation.get("z", 0))))
    rig.scale.x *= float(scale.get("x", 1))
    rig.scale.y *= float(scale.get("y", 1))
    rig.scale.z *= float(scale.get("z", 1))


def _assign_action(rig, action_name: str) -> None:
    if not action_name:
        return
    action = bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(f"Required Blender action is missing: {action_name}")
    rig.animation_data_create()
    rig.animation_data.action = action


def _face_object_towards(obj, target, frame_start: int, frame_end: int) -> None:
    direction = target.matrix_world.translation - obj.matrix_world.translation
    if direction.length < 0.001:
        return
    rotation = direction.to_track_quat("-Y", "Z").to_euler()
    obj.rotation_euler.z = rotation.z
    obj.keyframe_insert(data_path="rotation_euler", frame=frame_start, index=2)
    obj.keyframe_insert(data_path="rotation_euler", frame=frame_end, index=2)


def _apply_emotion(rig, emotion: str) -> None:
    # Blender string custom properties are metadata and cannot be keyframed.
    rig["emotion"] = emotion


def _apply_visemes(
    mouth,
    cues: list[dict[str, object]],
    *,
    fps: int,
    frame_start: int,
) -> None:
    if mouth is None or not cues:
        return
    shape_keys = getattr(getattr(mouth, "data", None), "shape_keys", None)
    key_blocks = shape_keys.key_blocks if shape_keys is not None else None
    viseme_names = []
    if key_blocks is not None:
        viseme_names = [key.name for key in key_blocks if key.name.startswith("viseme_")]

    for cue in cues:
        frame = frame_start + round(float(cue.get("time_seconds", 0)) * fps)
        name = str(cue.get("name", "REST"))
        weight = float(cue.get("weight", 1.0))
        if viseme_names:
            for key_name in viseme_names:
                key = key_blocks.get(key_name)
                if key is None:
                    continue
                key.value = 0.0
                key.keyframe_insert(data_path="value", frame=max(frame_start, frame - 1))
            selected = key_blocks.get(f"viseme_{name}")
            if selected is not None:
                selected.value = weight
                selected.keyframe_insert(data_path="value", frame=frame)
                selected.value = 0.0
                selected.keyframe_insert(
                    data_path="value",
                    frame=frame + max(1, round(fps * 0.08)),
                )
            continue

        mouth.scale.z = 0.25 if name == "REST" else 0.25 + (0.55 * weight)
        mouth.keyframe_insert(data_path="scale", frame=frame, index=2)


def _add_dialogue_audio(dialogue: dict[str, object], frame_start: int, fps: int) -> None:
    audio_path = str(dialogue.get("audio_path", ""))
    if not audio_path:
        return
    path = Path(audio_path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"Dialogue audio file is missing: {path}")
    scene = bpy.context.scene
    if scene.sequence_editor is None:
        scene.sequence_editor_create()
    start_seconds = float(dialogue.get("start_seconds", 0))
    start_frame = frame_start + round(start_seconds * fps)
    scene.sequence_editor.sequences.new_sound(
        name=f"dialogue-{path.stem}",
        filepath=str(path),
        channel=1,
        frame_start=start_frame,
    )


def _configure_character(
    cue: dict[str, object],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    rig = _object(str(cue["rig_object"]))
    anchor = _object(str(cue["anchor_object"]))
    _set_character_visibility(rig, True)
    _copy_anchor_transform(rig, anchor, dict(cue.get("transform_offset", {})))
    _assign_action(rig, str(cue.get("action_name", "")))
    _apply_emotion(rig, str(cue.get("emotion", "neutral")))

    target_name = str(cue.get("look_at_object", ""))
    target = _object(target_name, required=False) if target_name else None
    if target is not None:
        _face_object_towards(rig, target, frame_start, frame_end)

    dialogue = cue.get("dialogue")
    if isinstance(dialogue, dict):
        mouth_name = str(cue.get("mouth_object", ""))
        mouth = _object(mouth_name, required=False) if mouth_name else None
        _apply_visemes(
            mouth,
            list(dialogue.get("visemes", [])),
            fps=fps,
            frame_start=frame_start,
        )
        _add_dialogue_audio(dialogue, frame_start, fps)


def _configure_prop(cue: dict[str, object]) -> None:
    obj = _object(str(cue["object_name"]))
    visible = bool(cue.get("visible", True))
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    transform = cue.get("transform")
    if isinstance(transform, dict):
        _set_transform(obj, transform)

    parent_character = str(cue.get("parent_character", ""))
    parent_bone = str(cue.get("parent_bone", ""))
    if parent_character:
        parent = _object(parent_character)
        obj.parent = parent
        if parent_bone:
            obj.parent_type = "BONE"
            obj.parent_bone = parent_bone


def _camera_focus_point(target, preset: str) -> Vector:
    focus = target.matrix_world.translation.copy()
    focus.z += _CAMERA_FOCUS_HEIGHTS.get(preset, _CAMERA_FOCUS_HEIGHTS["wide"])
    return focus


def _configure_camera(cue: dict[str, object], frame_start: int, frame_end: int) -> None:
    camera = _object(str(cue["object_name"]))
    if camera.type != "CAMERA":
        raise RuntimeError(f"Configured camera object is not a camera: {camera.name}")
    bpy.context.scene.camera = camera

    start_transform = cue.get("start_transform")
    end_transform = cue.get("end_transform")
    if isinstance(start_transform, dict):
        _set_transform(camera, start_transform)
        camera.keyframe_insert(data_path="location", frame=frame_start)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame_start)
    if isinstance(end_transform, dict):
        _set_transform(camera, end_transform)
        camera.keyframe_insert(data_path="location", frame=frame_end)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame_end)

    preset = str(cue.get("preset", "wide")).lower()
    target_name = str(cue.get("look_at_object", ""))
    target = _object(target_name, required=False) if target_name else None
    if target is not None:
        focus = _camera_focus_point(target, preset)
        if preset == "close" and not isinstance(start_transform, dict):
            inward_sign = -1.0 if focus.x >= 0 else 1.0
            camera.location.x = focus.x + (inward_sign * _CLOSE_CAMERA_SIDE_OFFSET)
        direction = focus - camera.matrix_world.translation
        if direction.length >= 0.001:
            camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        print(
            "CAMERA_FOCUS="
            f"{target.name}:{preset}:"
            f"({focus.x:.3f},{focus.y:.3f},{focus.z:.3f})"
        )


def _timeline_frame(
    seconds: float,
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> int:
    frame = frame_start + round(seconds * fps)
    return min(frame_end, max(frame_start, frame))


def _apply_light_flicker(
    cue: dict[str, object],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    target = _object(str(cue["target_object"]))
    if target.type != "LIGHT" or target.data is None:
        raise RuntimeError(f"Timeline target is not a Blender light: {target.name}")
    values = [float(value) for value in cue.get("values", [])]
    if len(values) < 2:
        raise RuntimeError("Light flicker requires at least two energy multipliers")
    start_seconds = float(cue.get("start_seconds", 0.0))
    duration_seconds = float(cue.get("duration_seconds", 0.0))
    base_energy = float(target.data.energy)
    for index, multiplier in enumerate(values):
        progress = index / (len(values) - 1)
        seconds = start_seconds + (duration_seconds * progress)
        frame = _timeline_frame(
            seconds,
            fps=fps,
            frame_start=frame_start,
            frame_end=frame_end,
        )
        target.data.energy = base_energy * multiplier
        target.data.keyframe_insert(data_path="energy", frame=frame)
    print(
        f"TIMELINE_CUE=light_flicker:{target.name}:"
        f"{start_seconds:.3f}:{duration_seconds:.3f}:{len(values)}"
    )


def _apply_light_energy(
    cue: dict[str, object],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    target = _object(str(cue["target_object"]))
    if target.type != "LIGHT" or target.data is None:
        raise RuntimeError(f"Timeline target is not a Blender light: {target.name}")
    values = [float(value) for value in cue.get("values", [])]
    if len(values) != 1:
        raise RuntimeError("Light energy cue requires one target multiplier")
    seconds = float(cue.get("start_seconds", 0.0))
    frame = _timeline_frame(
        seconds,
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )
    target.data.energy = float(target.data.energy) * values[0]
    target.data.keyframe_insert(data_path="energy", frame=frame)
    print(f"TIMELINE_CUE=light_energy:{target.name}:{seconds:.3f}:{values[0]:.3f}")


def _apply_camera_push(
    cue: dict[str, object],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    camera = _object(str(cue["target_object"]))
    if camera.type != "CAMERA":
        raise RuntimeError(f"Timeline target is not a Blender camera: {camera.name}")
    parameters = dict(cue.get("parameters", {}))
    focus_name = str(parameters.get("focus_object", ""))
    focus = _object(focus_name)
    distance = float(parameters.get("distance", 0.0))
    if distance <= 0:
        raise RuntimeError("Camera push distance must be positive")

    start_seconds = float(cue.get("start_seconds", 0.0))
    duration_seconds = float(cue.get("duration_seconds", 0.0))
    start_key = _timeline_frame(
        start_seconds,
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )
    end_key = _timeline_frame(
        start_seconds + duration_seconds,
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )

    start_location = camera.location.copy()
    camera.location = start_location
    camera.keyframe_insert(data_path="location", frame=start_key)
    forward = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    if forward.length < 0.001:
        raise RuntimeError(f"Camera {camera.name} has no usable forward direction")
    camera.location = start_location + (forward.normalized() * distance)
    camera.keyframe_insert(data_path="location", frame=end_key)
    print(
        f"TIMELINE_CUE=camera_push:{camera.name}:{focus.name}:"
        f"{start_seconds:.3f}:{duration_seconds:.3f}:{distance:.3f}"
    )


def _apply_character_look(
    cue: dict[str, object],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    character = _object(str(cue["target_object"]))
    if character.type != "ARMATURE":
        raise RuntimeError(
            f"Timeline character-look target is not an armature: {character.name}"
        )
    parameters = dict(cue.get("parameters", {}))
    focus_name = str(parameters.get("focus_object", ""))
    focus = _object(focus_name)
    max_yaw_degrees = float(parameters.get("max_yaw_degrees", 65.0))
    if max_yaw_degrees <= 0 or max_yaw_degrees > 120:
        raise RuntimeError("Character look max_yaw_degrees must remain between 0 and 120")

    start_seconds = float(cue.get("start_seconds", 0.0))
    duration_seconds = float(cue.get("duration_seconds", 0.0))
    start_key = _timeline_frame(
        start_seconds,
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )
    end_key = _timeline_frame(
        start_seconds + duration_seconds,
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )

    start_yaw = float(character.rotation_euler.z)
    character.rotation_euler.z = start_yaw
    character.keyframe_insert(data_path="rotation_euler", frame=start_key, index=2)

    direction = focus.matrix_world.translation - character.matrix_world.translation
    direction.z = 0.0
    if direction.length < 0.001:
        raise RuntimeError(
            f"Character {character.name} cannot look toward coincident target {focus.name}"
        )
    desired_yaw = direction.to_track_quat("-Y", "Z").to_euler().z
    delta = (desired_yaw - start_yaw + math.pi) % (2 * math.pi) - math.pi
    max_yaw = math.radians(max_yaw_degrees)
    clamped_delta = max(-max_yaw, min(max_yaw, delta))
    character.rotation_euler.z = start_yaw + clamped_delta
    character.keyframe_insert(data_path="rotation_euler", frame=end_key, index=2)
    print(
        f"TIMELINE_CUE=character_look:{character.name}:{focus.name}:"
        f"{start_seconds:.3f}:{duration_seconds:.3f}:"
        f"{math.degrees(clamped_delta):.3f}"
    )


def _apply_timeline(
    cues: list[dict[str, object]],
    *,
    fps: int,
    frame_start: int,
    frame_end: int,
) -> None:
    handlers = {
        "light_flicker": _apply_light_flicker,
        "light_energy": _apply_light_energy,
        "camera_push": _apply_camera_push,
        "character_look": _apply_character_look,
    }
    for raw_cue in cues:
        cue = dict(raw_cue)
        kind = str(cue.get("kind", ""))
        handler = handlers.get(kind)
        if handler is None:
            raise RuntimeError(f"Unsupported Blender timeline cue kind: {kind}")
        handler(
            cue,
            fps=fps,
            frame_start=frame_start,
            frame_end=frame_end,
        )
    print(f"TIMELINE_CUES_APPLIED={len(cues)}")


def _configure_render(manifest: dict[str, object], output: Path) -> tuple[int, int, int]:
    render = dict(manifest["render"])
    scene = bpy.context.scene
    width = int(render["width"])
    height = int(render["height"])
    fps = int(render["fps"])
    duration_seconds = float(render["duration_seconds"])
    frame_start = 1
    frame_end = max(1, round(duration_seconds * fps))

    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.film_transparent = bool(render.get("transparent_background", False))

    desired_engine = str(render.get("engine", "BLENDER_EEVEE_NEXT"))
    try:
        scene.render.engine = desired_engine
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = int(render.get("samples", 32))

    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    return fps, frame_start, frame_end


def main() -> None:
    args = _arguments()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    character_cues = [dict(cue) for cue in manifest.get("characters", [])]
    _prepare_character_visibility(character_cues)

    fps, frame_start, frame_end = _configure_render(manifest, output_path)
    for cue in character_cues:
        _configure_character(
            cue,
            fps=fps,
            frame_start=frame_start,
            frame_end=frame_end,
        )
    for cue in manifest.get("props", []):
        _configure_prop(dict(cue))
    _configure_camera(dict(manifest["camera"]), frame_start, frame_end)
    _apply_timeline(
        [dict(cue) for cue in manifest.get("timeline", [])],
        fps=fps,
        frame_start=frame_start,
        frame_end=frame_end,
    )

    bpy.context.scene.frame_set(frame_start)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path.with_suffix(".prepared.blend")))
    bpy.ops.render.render(animation=True)
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Blender did not create the expected MP4: {output_path}")
    print(f"BLENDER_SHOT_SUCCEEDED={output_path}")


if __name__ == "__main__":
    main()
