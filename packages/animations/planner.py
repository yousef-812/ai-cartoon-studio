from packages.animations.models import AnimatedShotSpec, AnimationPlanRequest
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
                if keyframe.status != VisualAssetStatus.SUCCEEDED:
                    raise ValueError(
                        f"Keyframe for scene {scene.scene_number} shot {shot.number} is incomplete"
                    )
                if keyframe.review_status != VisualAssetReviewStatus.APPROVED:
                    raise ValueError(
                        f"Keyframe for scene {scene.scene_number} shot {shot.number} is not approved"
                    )
                if not keyframe.images or not keyframe.images[0].storage_path:
                    raise ValueError(
                        f"Keyframe for scene {scene.scene_number} shot {shot.number} is not stored"
                    )
                if shot.duration_seconds > request.max_clip_duration_seconds:
                    raise ValueError(
                        f"Scene {scene.scene_number} shot {shot.number} is {shot.duration_seconds}s; "
                        "split it in direction before animation"
                    )

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
