from packages.characters.models import CharacterRead, CharacterRole, VisualIdentity, VoiceProfile
from packages.direction.models import EpisodeDirection
from packages.series.models import SeriesRead, SeriesRules, SeriesStatus, VisualStyle
from packages.visuals.models import VisualAssetType
from packages.visuals.planner import VisualAssetPlanner


def test_visual_asset_planner_builds_references_backgrounds_and_keyframes() -> None:
    series = SeriesRead(
        name="Skykeepers",
        slug="skykeepers",
        logline="Friends protect a floating city powered by imagination.",
        synopsis="A serialized family adventure.",
        genre="adventure comedy",
        target_audience="family 8+",
        primary_language="en",
        status=SeriesStatus.ACTIVE,
        visual_style=VisualStyle(art_direction="Stylized cinematic 2D animation"),
        rules=SeriesRules(),
    )
    character = CharacterRead(
        series_id=series.id,
        name="Mira",
        role=CharacterRole.PROTAGONIST,
        age_range="12-14",
        description="A curious young inventor.",
        personality_traits=["curious", "brave"],
        visual_identity=VisualIdentity(
            reference_prompt="Teen inventor with round goggles and an amber jacket.",
            body_shape="small athletic silhouette",
            face="round face with large brown eyes",
            hair="dark curly bob",
            palette=["amber", "navy", "cream"],
            signature_features=["round goggles", "tool belt"],
        ),
        wardrobe={"default": "amber jacket, navy trousers, cream boots"},
        speaking_style="Fast and optimistic.",
        voice_profile=VoiceProfile(),
    )
    direction = EpisodeDirection(
        title="The Clockwork Cloud",
        total_estimated_duration_seconds=180,
        scenes=[
            {
                "scene_number": scene_number,
                "title": f"Scene {scene_number}",
                "estimated_duration_seconds": 60,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": scene_number,
                        "duration_seconds": 60,
                        "shot_size": "wide",
                        "camera_angle": "eye level",
                        "camera_movement": "locked",
                        "composition": "Mira is framed clearly against the cloud engine.",
                        "location": "Cloud Engine Room",
                        "characters": ["Mira"],
                        "action": "Mira studies a glowing control panel.",
                        "emotion": "focused concern",
                        "visual_prompt": "Mira beside the cloud engine in warm emergency light.",
                    }
                ],
            }
            for scene_number in (1, 2, 3)
        ],
    )

    specs = VisualAssetPlanner().plan(series, [character], [], direction)
    keys = {spec.key for spec in specs}

    assert "character:Mira:reference" in keys
    assert "character:Mira:expressions" in keys
    assert "location:Cloud Engine Room:background" in keys
    assert "shot:1:1:keyframe" in keys
    keyframe = next(spec for spec in specs if spec.asset_type == VisualAssetType.SHOT_KEYFRAME)
    assert keyframe.dependency_keys == [
        "location:Cloud Engine Room:background",
        "character:Mira:reference",
    ]
    assert keyframe.generation.width == 1280
    assert keyframe.generation.height == 720
