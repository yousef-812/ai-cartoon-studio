from packages.finalization.qc import (
    parse_integrated_loudness,
    parse_max_volume,
    parse_silence_durations,
)


def test_quality_control_parsers_extract_audio_metrics() -> None:
    stderr = """
    [silencedetect] silence_duration: 0.420
    [silencedetect] silence_duration: 1.750
    [Parsed_volumedetect] max_volume: -1.2 dB
    [Parsed_ebur128] I:         -17.1 LUFS
    [Parsed_ebur128] I:         -15.8 LUFS
    """

    assert parse_silence_durations(stderr) == [0.42, 1.75]
    assert parse_max_volume(stderr) == -1.2
    assert parse_integrated_loudness(stderr) == -15.8


def test_integrated_loudness_ignores_infinite_measurements() -> None:
    assert parse_integrated_loudness("I: -inf LUFS") is None
