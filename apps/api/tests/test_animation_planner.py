from packages.animations.models import AnimationPlanRequest
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


def test_animation_planner_requires_approved_stored_keyframes(tmp_path) -> None:
    scenes = []
    assets = []
    for scene_number in range(1, 4):
        keyframe_path = tmp_path / f"scene-{scene_number}.png"
        keyframe_path.write_bytes(b"keyframe")
        scenes.append(
            {
                "scene_number": scene_number,
                "title": f"Scene {scene_number}",
                "estimated_duration_seconds": 20,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": scene_number,
                        "duration_seconds": 20,
                        "shot_size": "medium",
                        "camera_angle": "eye level",
                        "camera_movement": "slow push in",
                        "composition": "Readable character silhouette against the environment.",
                        "location": "Workshop",
                        "characters": ["Mira"],
                        "action": "Mira carefully turns the control wheel.",
                        "emotion": "focused determination",
                        "visual_prompt": "Stylized 2D animation keyframe in a warm workshop.",
                        "animation_notes": ["Keep the hand motion slow and readable."],
                        "continuity_requirements": ["Amber jacket and round goggles remain unchanged."],
                    }
                ],
            }
        )
        assets.append(
            VisualAssetRead(
                id=f"asset-{scene_number}",
                series_id="series-1",
                direction_job_id="direction-1",
                status=VisualAssetStatus.SUCCEEDED,
                review_status=VisualAssetReviewStatus.APPROVED,
                provider="local-comfyui",
                attempts=1,
                spec=VisualAssetSpec(
                    key=f"shot:{scene_number}:1:keyframe",
                    asset_type=VisualAssetType.SHOT_KEYFRAME,
                    name=f"Scene {scene_number} shot 1 keyframe",
                    scene_number=scene_number,
                    shot_number=1,
                    generation=ImageGenerationSpec(
                        prompt="A stable production keyframe for animation.",
                        width=1280,
                        height=720,
                        seed=scene_number,
                    ),
                ),
                images=[
                    GeneratedImage(
                        url=(
                            f"/artifacts/series-1/visual-assets/asset-{scene_number}/01.png"
                        ),
                        filename=keyframe_path.name,
                        storage_path=str(keyframe_path),
                    )
                ],
            )
        )

    direction = EpisodeDirection(
        title="The Clockwork Cloud",
        total_estimated_duration_seconds=60,
        scenes=scenes,
    )
    specs = AnimationPlanner().plan(
        direction,
        assets,
        AnimationPlanRequest(fps=12, max_clip_duration_seconds=20),
    )

    assert len(specs) == 3
    assert specs[0].generation.input_image_path.endswith("scene-1.png")
    assert specs[0].generation.frame_count == 240
    assert specs[0].generation.metadata["camera_movement"] == "slow push in"
