from pathlib import Path

from packages.blender.models import BlenderSceneRegistry, BlenderShotManifest
from packages.blender.planner import BlenderShotPlanner
from packages.direction.models import EpisodeDirection
from packages.scripts.models import EpisodeScript, ScriptScene


def _dialogue_by_order(
    scene: ScriptScene,
    *,
    audio_root: Path | None,
) -> dict[int, dict[str, object]]:
    dialogue: dict[int, dict[str, object]] = {}
    for line in scene.dialogue:
        audio_path = ""
        if audio_root is not None:
            candidate = audio_root / f"scene_{scene.number:02d}_line_{line.order:02d}.wav"
            if candidate.is_file():
                audio_path = str(candidate.resolve())

        dialogue[line.order] = {
            "speaker": line.speaker,
            "text": line.text,
            "audio_path": audio_path,
            "start_seconds": 0.15,
            "duration_seconds": line.estimated_duration_seconds,
        }
    return dialogue


def build_episode_manifests(
    direction: EpisodeDirection,
    screenplay: EpisodeScript,
    registry: BlenderSceneRegistry,
    *,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
    render_engine: str = "BLENDER_EEVEE_NEXT",
    samples: int = 32,
    audio_root: Path | None = None,
) -> list[BlenderShotManifest]:
    script_scenes = {scene.number: scene for scene in screenplay.scenes}
    direction_scene_numbers = {scene.scene_number for scene in direction.scenes}
    missing_scenes = sorted(direction_scene_numbers - script_scenes.keys())
    if missing_scenes:
        raise ValueError(f"Screenplay is missing directed scenes: {missing_scenes}")

    planner = BlenderShotPlanner(registry)
    manifests: list[BlenderShotManifest] = []

    for directed_scene in direction.scenes:
        script_scene = script_scenes[directed_scene.scene_number]
        dialogue = _dialogue_by_order(script_scene, audio_root=audio_root)

        for shot in directed_scene.shots:
            manifest = planner.plan(
                shot,
                fps=fps,
                width=width,
                height=height,
                render_engine=render_engine,
                samples=samples,
                dialogue_by_order=dialogue,
            )
            metadata = {
                **manifest.metadata,
                "episode_title": direction.title,
                "scene_title": directed_scene.title,
                "source": "approved direction and screenplay",
            }
            manifests.append(manifest.model_copy(update={"metadata": metadata}))

    return manifests
