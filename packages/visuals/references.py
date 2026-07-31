from packages.images.models import ImageGenerationSpec
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewStatus,
    VisualAssetType,
)


def generation_with_approved_character_references(
    asset: VisualAssetRead,
    dependencies: list[VisualAssetRead | None],
) -> ImageGenerationSpec:
    dependency_map = {
        dependency.spec.key: dependency
        for dependency in dependencies
        if dependency is not None
    }
    reference_sources = list(asset.spec.generation.reference_urls)

    for key in asset.spec.dependency_keys:
        dependency = dependency_map.get(key)
        if dependency is None:
            raise ValueError(f"Required visual dependency is missing: {key}")
        if dependency.spec.asset_type != VisualAssetType.CHARACTER_REFERENCE:
            continue
        if dependency.review_status != VisualAssetReviewStatus.APPROVED:
            raise ValueError(f"Character reference is not approved: {key}")
        if not dependency.images:
            raise ValueError(f"Approved character reference has no image: {key}")

        image = dependency.images[0]
        source = image.storage_path or image.url
        if not source:
            raise ValueError(f"Approved character reference has no usable source: {key}")
        if source not in reference_sources:
            reference_sources.append(source)

    return asset.spec.generation.model_copy(
        update={"reference_urls": reference_sources}
    )
