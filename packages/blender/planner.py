from packages.blender.models import (
    BlenderCharacterCue,
    BlenderSceneRegistry,
    BlenderShotManifest,
    CameraCue,
    DialogueTrack,
    RenderSettings,
)
from packages.blender.visemes import build_viseme_cues
from packages.direction.models import ShotPlan


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
    ) -> BlenderShotManifest:
        camera_preset = self._camera_preset(shot.shot_size)
        camera_object = self.registry.camera_object(camera_preset)
        dialogue_by_order = dialogue_by_order or {}

        speaker_name, dialogue = self._dialogue_for_shot(shot, dialogue_by_order)
        characters: list[BlenderCharacterCue] = []
        for index, name in enumerate(shot.characters):
            registered = self.registry.character(name)
            anchor_key = self._anchor_key(name, index, len(shot.characters), registered.anchors)
            anchor_object = registered.anchors.get(anchor_key) or registered.default_anchor
            if not anchor_object:
                raise ValueError(f"Character '{name}' has no usable Blender anchor")

            action_key = self._action_key(shot, name, speaker_name)
            action_name = registered.actions.get(action_key) or registered.actions.get("idle", "")
            look_at_object = self._look_at_object(shot.characters, name)
            dialogue_track = None
            if dialogue is not None and name == speaker_name:
                text = str(dialogue.get("text", ""))
                start_seconds = float(dialogue.get("start_seconds", 0.15))
                duration_seconds = float(
                    dialogue.get(
                        "duration_seconds",
                        max(0.2, shot.duration_seconds - start_seconds - 0.15),
                    )
                )
                duration_seconds = min(
                    duration_seconds,
                    max(0.0, shot.duration_seconds - start_seconds),
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

        return BlenderShotManifest(
            scene_number=shot.scene_number,
            shot_number=shot.number,
            shot_key=f"scene:{shot.scene_number}:shot:{shot.number}",
            render=RenderSettings(
                width=width,
                height=height,
                fps=fps,
                duration_seconds=shot.duration_seconds,
                engine=render_engine,
                samples=samples,
            ),
            camera=CameraCue(
                preset=camera_preset,
                object_name=camera_object,
                look_at_object=self._camera_target(shot.characters),
                movement=shot.camera_movement,
            ),
            characters=characters,
            metadata={
                "shot_size": shot.shot_size,
                "camera_angle": shot.camera_angle,
                "composition": shot.composition,
                "visible_action": shot.action,
                "transition": shot.transition,
                "continuity_requirements": shot.continuity_requirements,
            },
        )

    @staticmethod
    def _camera_preset(shot_size: str) -> str:
        lowered = shot_size.lower()
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

    def _look_at_object(self, names: list[str], current: str) -> str:
        for name in names:
            if name == current:
                continue
            return self.registry.character(name).rig_object
        return ""

    def _camera_target(self, names: list[str]) -> str:
        if not names:
            return ""
        if len(names) == 1:
            return self.registry.character(names[0]).rig_object
        return "ANCHOR_Workbench_Center"
