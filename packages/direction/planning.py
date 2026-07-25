from __future__ import annotations

from packages.direction.models import DirectionGenerationRequest
from packages.scripts.models import EpisodeScript


def allocate_shots(
    script: EpisodeScript,
    request: DirectionGenerationRequest,
) -> list[int] | None:
    """Allocate an exact target shot count across screenplay scenes.

    Every scene receives at least one shot and enough individual shots to carry
    each dialogue line without overlap. Remaining shots are distributed by
    screenplay scene duration so longer scenes receive proportionally more
    visual coverage.
    """

    target = request.target_shot_count
    if target is None:
        return None

    minimums = [max(1, len(scene.dialogue)) for scene in script.scenes]
    minimum_total = sum(minimums)
    if minimum_total > target:
        raise ValueError(
            f"The screenplay needs at least {minimum_total} shots to preserve all scenes "
            f"and dialogue, but the direction request allows only {target}"
        )

    counts = minimums[:]
    remaining = target - minimum_total
    while remaining:
        scene_index = max(
            range(len(script.scenes)),
            key=lambda index: (
                script.scenes[index].estimated_duration_seconds / counts[index],
                -index,
            ),
        )
        counts[scene_index] += 1
        remaining -= 1

    return counts


def constrained_shot_duration(
    script: EpisodeScript,
    request: DirectionGenerationRequest,
) -> float | None:
    """Return one legal uniform shot duration for an exact-count plan."""

    target = request.target_shot_count
    if target is None:
        return None

    desired = script.total_estimated_duration_seconds / target
    duration = min(
        request.max_shot_duration_seconds,
        max(request.min_shot_duration_seconds, desired),
    )
    duration = round(float(duration), 3)
    total = duration * target
    if total < 30:
        raise ValueError(
            "The requested shot count and duration range cannot produce a valid "
            "30-second minimum direction plan"
        )
    return duration
