import pytest

from packages.images.models import GeneratedImage, ImageGenerationSpec
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewStatus,
    VisualAssetSpec,
    VisualAssetStatus,
    VisualAssetType,
)
from packages.visuals.references import generation_with_approved_character_references


def _asset(
    *,
    asset_id: str,
    spec: VisualAssetSpec,
    status: VisualAssetStatus,
    review_status: VisualAssetReviewStatus,
    images: list[GeneratedImage] | None = None,
) -> VisualAssetRead:
    return VisualAssetRead(
        id=asset_id,
        series_id="series-1",
        direction_job_id="direction-1",
        status=status,
        review_status=review_status,
        provider="local-comfyui",
        attempts=1,
        spec=spec,
        images=images or [],
    )


def test_generation_uses_only_approved_character_reference_images() -> None:
    character_key = "character:Omar:reference"
    background_key = "location:Workshop:background"
    shot = _asset(
        asset_id="shot-1",
        status=VisualAssetStatus.BLOCKED,
        review_status=VisualAssetReviewStatus.PENDING_REVIEW,
        spec=VisualAssetSpec(
            key="shot:1:1:keyframe",
            asset_type=VisualAssetType.SHOT_KEYFRAME,
            name="Shot 1 keyframe",
            dependency_keys=[background_key, character_key],
            generation=ImageGenerationSpec(
                prompt="Omar stands beside the emergency lamp in the workshop."
            ),
        ),
    )
    character = _asset(
        asset_id="character-1",
        status=VisualAssetStatus.SUCCEEDED,
        review_status=VisualAssetReviewStatus.APPROVED,
        spec=VisualAssetSpec(
            key=character_key,
            asset_type=VisualAssetType.CHARACTER_REFERENCE,
            name="Omar permanent character reference",
            generation=ImageGenerationSpec(
                prompt="A permanent full-body reference image of Omar."
            ),
        ),
        images=[
            GeneratedImage(
                url="/artifacts/series-1/omar.png",
                storage_path="/workspace/storage/series-1/omar.png",
            )
        ],
    )
    background = _asset(
        asset_id="background-1",
        status=VisualAssetStatus.SUCCEEDED,
        review_status=VisualAssetReviewStatus.APPROVED,
        spec=VisualAssetSpec(
            key=background_key,
            asset_type=VisualAssetType.BACKGROUND,
            name="Workshop master background",
            generation=ImageGenerationSpec(
                prompt="A reusable workshop animation background with no people."
            ),
        ),
        images=[GeneratedImage(url="/artifacts/series-1/workshop.png")],
    )

    generation = generation_with_approved_character_references(
        shot,
        [background, character],
    )

    assert generation.reference_urls == ["/workspace/storage/series-1/omar.png"]


def test_generation_rejects_approved_character_reference_without_image() -> None:
    character_key = "character:Nader:reference"
    shot = _asset(
        asset_id="shot-2",
        status=VisualAssetStatus.BLOCKED,
        review_status=VisualAssetReviewStatus.PENDING_REVIEW,
        spec=VisualAssetSpec(
            key="shot:1:2:keyframe",
            asset_type=VisualAssetType.SHOT_KEYFRAME,
            name="Shot 2 keyframe",
            dependency_keys=[character_key],
            generation=ImageGenerationSpec(
                prompt="Nader looks toward the emergency lamp with concern."
            ),
        ),
    )
    character = _asset(
        asset_id="character-2",
        status=VisualAssetStatus.SUCCEEDED,
        review_status=VisualAssetReviewStatus.APPROVED,
        spec=VisualAssetSpec(
            key=character_key,
            asset_type=VisualAssetType.CHARACTER_REFERENCE,
            name="Nader permanent character reference",
            generation=ImageGenerationSpec(
                prompt="A permanent full-body reference image of Nader."
            ),
        ),
    )

    with pytest.raises(ValueError, match="has no image"):
        generation_with_approved_character_references(shot, [character])
