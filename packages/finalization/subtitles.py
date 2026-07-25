from packages.finalization.models import SubtitleCue


def _timestamp(seconds: float, separator: str) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def render_srt(cues: list[SubtitleCue]) -> str:
    blocks: list[str] = []
    for cue in cues:
        speaker = f"{cue.speaker}: " if cue.speaker else ""
        blocks.append(
            f"{cue.index}\n{_timestamp(cue.start_time_seconds, ',')} --> "
            f"{_timestamp(cue.end_time_seconds, ',')}\n{speaker}{cue.text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_vtt(cues: list[SubtitleCue]) -> str:
    blocks = ["WEBVTT"]
    for cue in cues:
        speaker = f"<v {cue.speaker}>{cue.text}" if cue.speaker else cue.text
        blocks.append(
            f"{_timestamp(cue.start_time_seconds, '.')} --> "
            f"{_timestamp(cue.end_time_seconds, '.')}\n{speaker}"
        )
    return "\n\n".join(blocks) + "\n"
