from pathlib import Path

from packages.animations.models import AnimationEngine, AnimationPlanRequest
from packages.animations.planner import AnimationPlanner
from packages.direction.models import EpisodeDirection
from packages.images.models import GeneratedImage, ImageGenerationSpec
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewStatus,
    VisualAssetSpec,
    VisualAssetStatus,
    VisualAssetType,
)

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "demo" / "first-real-episode" / "blender" / "scene_registry.json"


def test_animation_planner_builds_blender_scene_jobs(tmp_path) -> None:
    scene_path = tmp_path / "workshop.blend"
    scene_path.write_bytes(b"blend")
    background_path = tmp_path / "workshop-concept.png"
    background_path.write_bytes(b"png")

    direction = EpisodeDirection(
        title="Reusable workshop",
        total_estimated_duration_seconds=30,
        scenes=[
            {
                "scene_number": scene_number,
                "title": f"Scene {scene_number}",
                "estimated_duration_seconds": 10,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": scene_number,
                        "duration_seconds": 10,
                        "shot_size": "wide",
                        "camera_angle": "eye level",
                        "camera_movement": "locked",
                        "composition": "Omar and Nader stand beside the workbench.",
                        "location": "ورشة النور",
                        "characters": ["عمر", "نادر"],
                        "action": "عمر يشرح بينما نادر يستمع.",
                        "emotion": "focused",
                        "dialogue_line_orders": [scene_number],
                        "visual_prompt": "The permanent workshop with both registered characters.",
                    }
                ],
            }
            for scene_number in (1, 2, 3)
        ],
    )
    background = VisualAssetRead(
        id="background-1",
        series_id="series-1",
        direction_job_id="direction-1",
        status=VisualAssetStatus.SUCCEEDED,
        review_status=VisualAssetReviewStatus.APPROVED,
        provider="local-comfyui",
        attempts=1,
        spec=VisualAssetSpec(
            key="location:ورشة النور:background",
            asset_type=VisualAssetType.BACKGROUND,
            name="Workshop master background",
            location_name="ورشة النور",
            generation=ImageGenerationSpec(
                prompt="A permanent workshop environment concept for Blender production."
            ),
        ),
        images=[
            GeneratedImage(
                url="/artifacts/workshop.png",
                storage_path=str(background_path),
            )
        ],
    )
    request = AnimationPlanRequest(
        engine=AnimationEngine.BLENDER,
        fps=24,
        max_clip_duration_seconds=12,
        blender_scene_path=str(scene_path),
        blender_registry_path=str(REGISTRY_PATH),
    )

    specs = AnimationPlanner().plan(direction, [background], request)

    assert len(specs) == 3
    assert all(spec.keyframe_asset_id == background.id for spec in specs)
    assert all(spec.generation.input_scene_path == str(scene_path.resolve()) for spec in specs)
    assert all(spec.generation.metadata["engine"] == "blender" for spec in specs)
    manifest = specs[0].generation.metadata["blender_manifest"]
    assert isinstance(manifest, dict)
    assert manifest["camera"]["object_name"] == "CAM_Wide"
    assert [cue["action_name"] for cue in manifest["characters"]] == [
        "Omar_Talk",
        "Nader_Listen",
    ]
