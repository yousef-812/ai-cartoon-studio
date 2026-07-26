import re

from packages.blender.models import VisemeCue


_VISEME_GROUPS: tuple[tuple[str, str], ...] = (
    ("M", "بمpbm"),
    ("F", "فfv"),
    ("O", "وؤou"),
    ("A", "اأإآعحهةaei"),
    ("L", "للنرldt"),
    ("S", "سصزذثظتطجشكدقخغszcjkgq"),
)


def _viseme_for_character(character: str) -> str:
    lowered = character.lower()
    for name, members in _VISEME_GROUPS:
        if lowered in members:
            return name
    return "REST"


def build_viseme_cues(
    text: str,
    *,
    start_seconds: float,
    duration_seconds: float,
) -> list[VisemeCue]:
    """Build a deterministic mouth-shape timeline.

    This is a lightweight fallback used before a phoneme aligner is available. It deliberately
    keeps the contract stable so a later forced-alignment provider can replace only this function.
    """

    if start_seconds < 0:
        raise ValueError("Viseme start time cannot be negative")
    if duration_seconds <= 0:
        return []

    characters = [char for char in re.sub(r"\s+", "", text) if char.isalnum()]
    if not characters:
        return [
            VisemeCue(time_seconds=start_seconds, name="REST", weight=0.0),
            VisemeCue(
                time_seconds=start_seconds + duration_seconds,
                name="REST",
                weight=0.0,
            ),
        ]

    lead = min(0.08, duration_seconds * 0.08)
    active_duration = max(0.01, duration_seconds - (lead * 2))
    step = active_duration / len(characters)
    cues = [VisemeCue(time_seconds=start_seconds, name="REST", weight=0.0)]

    previous = "REST"
    for index, character in enumerate(characters):
        name = _viseme_for_character(character)
        cue_time = start_seconds + lead + (index * step)
        if name == previous:
            continue
        cues.append(VisemeCue(time_seconds=cue_time, name=name, weight=1.0))
        previous = name

    cues.append(
        VisemeCue(
            time_seconds=start_seconds + duration_seconds,
            name="REST",
            weight=0.0,
        )
    )
    return cues
