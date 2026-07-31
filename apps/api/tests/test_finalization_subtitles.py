import pytest
from pydantic import ValidationError

from packages.finalization.models import FinalizationPlanRequest, SubtitleCue
from packages.finalization.subtitles import render_srt, render_vtt


def test_subtitle_renderers_preserve_timing_and_speaker() -> None:
    cues = [
        SubtitleCue(
            index=1,
            start_time_seconds=1.25,
            end_time_seconds=3.75,
            text="We made it.",
            speaker="Mira",
        )
    ]

    srt = render_srt(cues)
    vtt = render_vtt(cues)

    assert "00:00:01,250 --> 00:00:03,750" in srt
    assert "Mira: We made it." in srt
    assert vtt.startswith("WEBVTT")
    assert "00:00:01.250 --> 00:00:03.750" in vtt
    assert "<v Mira>We made it." in vtt


def test_burned_subtitles_require_subtitle_generation() -> None:
    with pytest.raises(ValidationError):
        FinalizationPlanRequest(
            include_subtitles=False,
            burn_subtitles=True,
        )
