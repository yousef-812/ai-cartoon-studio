from pathlib import Path

from packages.animations.models import (
    AnimatedShotSpec,
    AnimationEngine,
    AnimationPlanRequest,
)
from packages.blender.models import BlenderSceneRegistry
from packages.blender.planner import BlenderShotPlanner
from packages.direction.models import EpisodeDirection
from packages.videos.models import VideoGenerationSpec
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewStatus,
    VisualAssetStatus,
    VisualAssetType,
)


class AnimationPlanner:
    def plan(
        self,
        direction: EpisodeDirection,
        visual_assets: list[VisualAssetRead],
        request: AnimationPlanRequest,
    ) -> list[AnimatedShotSpec]:
        if request.engine == AnimationEngine.BLENDER:
            return self._plan_blender(direction, visual_assets, request)
        return self._plan_image_to_video(direction, visual_assets, request)

    def _plan_image_to_video(
        self,
        direction: EpisodeDirection,
        visual_assets: list[VisualAssetRead],
        request: AnimationPlanRequest,
    ) -> list[AnimatedShotSpec]:
        keyframes = {
            (asset.spec.scene_number, asset.spec.shot_number): asset
            for asset in visual_assets
            if asset.spec.asset_type == VisualAssetType.SHOT_KEYFRAME
        }
        specs: list[AnimatedShotSpec] = []
        for scene in direction.scenes:
            for shot in scene.shots:
                keyframe = keyframes.get((scene.scene_number, shot.number))
                if keyframe is None:
                    raise ValueError(
                        f"Missing keyframe for scene {scene.scene_number} shot {shot.number}"
                    )
                self._validate_source_asset(
                    keyframe,
                    f"Keyframe for scene {scene.scene_number} shot {shot.number}",
                )
                self._validate_duration(shot.duration_seconds, request)

                constraints = ". ".join(request.constraints)
                animation_notes = ". ".join(shot.animation_notes)
                continuity = ". ".join(shot.continuity_requirements)
                prompt = (
                    "Animate the supplied production keyframe without changing character identity, "
                    "wardrobe, colors, anatomy, environment design, composition, or lighting. "
                    f"Visible action: {shot.action}. Emotional intent: {shot.emotion}. "
                    f"Camera movement: {shot.camera_movement}. Shot size: {shot.shot_size}. "
                    f"Animation notes: {animation_notes}. Continuity: {continuity}. "
                    f"Additional constraints: {constraints}. Keep motion physically readable and "
                    "stable across all frames; no cuts, no text, no new characters."
                )
                negative_prompt = (
                    "identity drift, face drift, costume change, color shift, duplicated character, "
                    "extra limbs, warped hands, camera jump, background morphing, flicker, subtitles, "
                    "text, watermark, logo, hard cut, scene change"
                )
                image = keyframe.images[0]
                specs.append(
                    AnimatedShotSpec(
                        key=f"scene:{scene.scene_number}:shot:{shot.number}:animation",
                        scene_number=scene.scene_number,
                        shot_number=shot.number,
                        keyframe_asset_id=keyframe.id,
                        generation=VideoGenerationSpec(
                            input_image_path=image.storage_path,
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            width=keyframe.spec.generation.width,
                            height=keyframe.spec.generation.height,
                            duration_seconds=shot.duration_seconds,
                            fps=request.fps,
                            seed=keyframe.spec.generation.seed,
                            steps=request.steps,
                            guidance_scale=request.guidance_scale,
                            motion_strength=request.motion_strength,
                            metadata={
                                "engine": AnimationEngine.IMAGE_TO_VIDEO.value,
                                "scene_number": scene.scene_number,
                                "shot_number": shot.number,
                                "keyframe_asset_id": keyframe.id,
                                "characters": shot.characters,
                                "location": shot.location,
                                "camera_movement": shot.camera_movement,
                            },
                        ),
                    )
                )
        return specs

    def _plan_blender(
        self,
        direction: EpisodeDirection,
        visual_assets: list[VisualAssetRead],
        request: AnimationPlanRequest,
    ) -> list[AnimatedShotSpec]:
        scene_path = Path(request.blender_scene_path).expanduser().resolve()
        registry_path = Path(request.blender_registry_path).expanduser().resolve()
        if not scene_path.is_file():
            raise ValueError(f"Blender scene file is missing: {scene_path}")
        if not registry_path.is_file():
            raise ValueError(f"Blender scene registry is missing: {registry_path}")
        registry = BlenderSceneRegistry.model_validate_json(
            registry_path.read_text(encoding="utf-8")
        )
        shot_planner = BlenderShotPlanner(registry)
        backgrounds = {
            asset.spec.location_name: asset
            for asset in visual_assets
            if asset.spec.asset_type == VisualAssetType.BACKGROUND
        }

        specs: list[AnimatedShotSpec] = []
        for scene in direction.scenes:
            for shot in scene.shots:
                self._validate_duration(shot.duration_seconds, request)
                background = backgrounds.get(shot.location)
                if background is None:
                    raise ValueError(
                        f"Missing approved environment concept for Blender location {shot.location}"
                    )
                self._validate_source_asset(
                    background,
                    f"Environment concept for {shot.location}",
                )
                manifest = shot_planner.plan(
                    shot,
                    fps=request.fps,
                    width=request.width,
                    height=request.height,
                    render_engine=request.blender_render_engine,
                    samples=request.blender_samples,
                )
                specs.append(
                    AnimatedShotSpec(
                        key=f"scene:{scene.scene_number}:shot:{shot.number}:blender",
                        scene_number=scene.scene_number,
                        shot_number=shot.number,
                        keyframe_asset_id=background.id,
                        generation=VideoGenerationSpec(
                            input_image_path=background.images[0].storage_path,
                            input_scene_path=str(scene_path),
                            prompt=(
                                "Render the registered reusable Blender scene using permanent rigs, "
                                "approved character actions, camera presets, props, and lighting."
                            ),
                            width=request.width,
                            height=request.height,
                            duration_seconds=shot.duration_seconds,
                            fps=request.fps,
                            seed=-1,
                            steps=1,
                            guidance_scale=0,
                            motion_strength=0,
                            metadata={
                                "engine": AnimationEngine.BLENDER.value,
                                "scene_number": scene.scene_number,
                                "shot_number": shot.number,
                                "source_environment_asset_id": background.id,
                                "scene_registry_path": str(registry_path),
                                "characters": shot.characters,
                                "location": shot.location,
                                "blender_manifest": manifest.model_dump(mode="json"),
                            },
                        ),
                    )
                )
        return specs

    @staticmethod
    def _validate_duration(duration_seconds: float, request: AnimationPlanRequest) -> None:
        if duration_seconds > request.max_clip_duration_seconds:
            raise ValueError(
                f"Shot is {duration_seconds}s; split it in direction before animation"
            )

    @staticmethod
    def _validate_source_asset(asset: VisualAssetRead, label: str) -> None:
        if asset.status != VisualAssetStatus.SUCCEEDED:
            raise ValueError(f"{label} is incomplete")
        if asset.review_status != VisualAssetReviewStatus.APPROVED:
            raise ValueError(f"{label} is not approved")
        if not asset.images or not asset.images[0].storage_path:
            raise ValueError(f"{label} is not stored")
