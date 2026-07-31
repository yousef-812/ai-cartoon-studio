from packages.blender.models import (
    BlenderCharacterCue,
    BlenderSceneRegistry,
    BlenderShotManifest,
    CameraCue,
    DialogueTrack,
    RenderSettings,
    TimelineCue,
)
from packages.blender.visemes import build_viseme_cues
from packages.direction.models import ShotPlan

_DIALOGUE_TAIL_SECONDS = 0.20
_MAX_SHOT_DURATION_SECONDS = 60.0


class BlenderShotPlanner:
    def __init__(self, registry: BlenderSceneRegistry) -> None:
        self.registry = registry

    def plan(
        self,
        shot: ShotPlan,
        *,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        render_engine: str = "BLENDER_EEVEE_NEXT",
        samples: int = 32,
        dialogue_by_order: dict[int, dict[str, object]] | None = None,
        timeline: list[TimelineCue] | None = None,
    ) -> BlenderShotManifest:
        camera_preset = self._camera_preset(shot.shot_size)
        camera_object = self.registry.camera_object(camera_preset)
        dialogue_by_order = dialogue_by_order or {}
        timeline = timeline or []

        speaker_name, dialogue = self._dialogue_for_shot(shot, dialogue_by_order)
        render_duration = self._render_duration(shot.duration_seconds, dialogue)
        characters: list[BlenderCharacterCue] = []
        anchor_by_name: dict[str, str] = {}
        for index, name in enumerate(shot.characters):
            registered = self.registry.character(name)
            anchor_key = self._anchor_key(name, index, len(shot.characters), registered.anchors)
            anchor_object = registered.anchors.get(anchor_key) or registered.default_anchor
            if not anchor_object:
                raise ValueError(f"Character '{name}' has no usable Blender anchor")
            anchor_by_name[name] = anchor_object

            action_key = self._action_key(shot, name, speaker_name)
            action_name = registered.actions.get(action_key) or registered.actions.get("idle", "")
            look_at_object = self._look_at_object(
                shot.characters,
                name,
                speaker_name=speaker_name,
                camera_object=camera_object,
                camera_preset=camera_preset,
            )
            dialogue_track = None
            if dialogue is not None and name == speaker_name:
                text = str(dialogue.get("text", ""))
                start_seconds = float(dialogue.get("start_seconds", 0.15))
                duration_seconds = float(
                    dialogue.get(
                        "duration_seconds",
                        max(0.2, shot.duration_seconds - start_seconds - _DIALOGUE_TAIL_SECONDS),
                    )
                )
                dialogue_track = DialogueTrack(
                    speaker=name,
                    text=text,
                    audio_path=str(dialogue.get("audio_path", "")),
                    start_seconds=start_seconds,
                    duration_seconds=duration_seconds,
                    visemes=build_viseme_cues(
                        text,
                        start_seconds=start_seconds,
                        duration_seconds=duration_seconds,
                    ),
                )

            characters.append(
                BlenderCharacterCue(
                    name=name,
                    rig_object=registered.rig_object,
                    mouth_object=registered.mouth_object,
                    head_bone=registered.head_bone,
                    anchor_object=anchor_object,
                    action_name=action_name,
                    emotion=shot.emotion,
                    look_at_object=look_at_object,
                    dialogue=dialogue_track,
                )
            )

        camera_target = self._camera_target(
            shot.characters,
            anchor_by_name=anchor_by_name,
            speaker_name=speaker_name,
            shot_size=shot.shot_size,
        )
        return BlenderShotManifest(
            scene_number=shot.scene_number,
            shot_number=shot.number,
            shot_key=f"scene:{shot.scene_number}:shot:{shot.number}",
            render=RenderSettings(
                width=width,
                height=height,
                fps=fps,
                duration_seconds=render_duration,
                engine=render_engine,
                samples=samples,
            ),
            camera=CameraCue(
                preset=camera_preset,
                object_name=camera_object,
                look_at_object=camera_target,
                movement=shot.camera_movement,
            ),
            characters=characters,
            timeline=timeline,
            metadata={
                "shot_size": shot.shot_size,
                "camera_angle": shot.camera_angle,
                "composition": shot.composition,
                "visible_action": shot.action,
                "transition": shot.transition,
                "continuity_requirements": shot.continuity_requirements,
                "direction_duration_seconds": shot.duration_seconds,
                "render_duration_seconds": render_duration,
                "camera_target_object": camera_target,
                "timeline_cue_count": len(timeline),
            },
        )

    @staticmethod
    def _render_duration(
        direction_duration_seconds: float,
        dialogue: dict[str, object] | None,
    ) -> float:
        duration = float(direction_duration_seconds)
        if dialogue is not None:
            start = float(dialogue.get("start_seconds", 0.15))
            speech = float(dialogue.get("duration_seconds", 0.0))
            duration = max(duration, start + speech + _DIALOGUE_TAIL_SECONDS)
        if duration > _MAX_SHOT_DURATION_SECONDS:
            raise ValueError(
                f"Blender shot requires {duration:.3f}s, exceeding the "
                f"{_MAX_SHOT_DURATION_SECONDS:.0f}s shot limit"
            )
        return duration

    @staticmethod
    def _camera_preset(shot_size: str) -> str:
        lowered = shot_size.lower()
        if any(token in lowered for token in ("medium close", "medium-close", "متوسط قريب")):
            return "medium"
        if any(token in lowered for token in ("close", "قريب", "تفصيل")):
            return "close"
        if any(token in lowered for token in ("medium", "متوسط")):
            return "medium"
        return "wide"

    @staticmethod
    def _anchor_key(
        name: str,
        index: int,
        character_count: int,
        available: dict[str, str],
    ) -> str:
        if character_count == 1:
            for candidate in ("center", "workbench_center", "default"):
                if candidate in available:
                    return candidate
        candidates = ("left", "workbench_left") if index == 0 else ("right", "workbench_right")
        for candidate in candidates:
            if candidate in available:
                return candidate
        for candidate in (
            "left",
            "workbench_left",
            "right",
            "workbench_right",
            "center",
            "workbench_center",
            "default",
        ):
            if candidate in available:
                return candidate
        return next(iter(available), "")

    @staticmethod
    def _dialogue_for_shot(
        shot: ShotPlan,
        dialogue_by_order: dict[int, dict[str, object]],
    ) -> tuple[str, dict[str, object] | None]:
        for order in shot.dialogue_line_orders:
            dialogue = dialogue_by_order.get(order)
            if dialogue is None:
                continue
            speaker = dialogue.get("speaker")
            if isinstance(speaker, str) and speaker in shot.characters:
                return speaker, dialogue
        if shot.dialogue_line_orders and shot.characters:
            return shot.characters[0], {"speaker": shot.characters[0], "text": ""}
        return "", None

    @staticmethod
    def _action_key(shot: ShotPlan, name: str, speaker_name: str) -> str:
        if name == speaker_name:
            return "talk"
        if speaker_name:
            return "listen"

        text = f"{shot.action} {' '.join(shot.animation_notes)}".lower()
        keyword_actions = (
            (("point", "يشير", "أشار"), "point"),
            (("pick", "يلتقط", "يمسك", "يرفع"), "pick_up"),
            (("walk", "يمشي", "يتقدم"), "walk"),
            (("surpris", "مندهش", "يفاجأ"), "surprised"),
            (("worr", "قلق", "متوتر"), "worried"),
        )
        for keywords, action in keyword_actions:
            if any(keyword in text for keyword in keywords):
                return action
        return "idle"

    def _look_at_object(
        self,
        names: list[str],
        current: str,
        *,
        speaker_name: str,
        camera_object: str,
        camera_preset: str,
    ) -> str:
        if current == speaker_name and camera_preset in {"medium", "close"}:
            return camera_object
        if speaker_name and current != speaker_name:
            return self.registry.character(speaker_name).rig_object
        for name in names:
            if name == current:
                continue
            return self.registry.character(name).rig_object
        return camera_object if camera_preset == "close" else ""

    @staticmethod
    def _camera_target(
        names: list[str],
        *,
        anchor_by_name: dict[str, str],
        speaker_name: str,
        shot_size: str,
    ) -> str:
        if not names:
            return ""

        lowered = shot_size.lower()
        group_tokens = (
            "wide",
            "two shot",
            "two-shot",
            "reaction",
            "لقطة واسعة",
            "لقطة ثنائية",
        )
        if len(names) > 1 and (
            not speaker_name or any(token in lowered for token in group_tokens)
        ):
            return "ANCHOR_Workbench_Center"

        focus_name = speaker_name or names[0]
        return anchor_by_name.get(focus_name, "")
