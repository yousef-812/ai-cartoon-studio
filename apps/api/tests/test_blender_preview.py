from pathlib import Path

import pytest

from packages.blender.preview import (
    build_preview_command,
    select_preview_items,
    write_concat_manifest,
)


def _sequence() -> dict[str, object]:
    return {
        "shot_count": 3,
        "items": [
            {
                "scene_number": 1,
                "shot_number": 1,
                "shot_key": "scene:1:shot:1",
                "duration_seconds": 4.0,
                "output": "scene_01_shot_01.mp4",
            },
            {
                "scene_number": 1,
                "shot_number": 2,
                "shot_key": "scene:1:shot:2",
                "duration_seconds": 4.0,
                "output": "scene_01_shot_02.mp4",
            },
            {
                "scene_number": 2,
                "shot_number": 1,
                "shot_key": "scene:2:shot:1",
                "duration_seconds": 4.0,
                "output": "scene_02_shot_01.mp4",
            },
        ],
    }


def test_preview_selects_ordered_rendered_shots(tmp_path: Path) -> None:
    for name in (
        "scene_01_shot_01.mp4",
        "scene_01_shot_02.mp4",
        "scene_02_shot_01.mp4",
    ):
        (tmp_path / name).write_bytes(b"video")

    items = select_preview_items(_sequence(), tmp_path, limit=2)

    assert [Path(str(item["video_path"])).name for item in items] == [
        "scene_01_shot_01.mp4",
        "scene_01_shot_02.mp4",
    ]


def test_preview_rejects_missing_selected_shot(tmp_path: Path) -> None:
    (tmp_path / "scene_01_shot_01.mp4").write_bytes(b"video")

    with pytest.raises(FileNotFoundError, match="scene_01_shot_02.mp4"):
        select_preview_items(_sequence(), tmp_path, limit=2)


def test_preview_command_ignores_audio_and_normalizes_video(tmp_path: Path) -> None:
    items = []
    for name in ("scene_01_shot_01.mp4", "scene_01_shot_02.mp4"):
        path = tmp_path / name
        path.write_bytes(b"video")
        items.append({"video_path": str(path.resolve())})

    concat = tmp_path / "preview.concat.txt"
    write_concat_manifest(items, concat)
    command = build_preview_command(
        concat,
        tmp_path / "preview.mp4",
        width=1280,
        height=720,
        fps=24,
    )

    assert concat.read_text(encoding="utf-8").count("file '") == 2
    assert "-an" in command
    assert "libx264" in command
    assert "scale=1280:720" in command[command.index("-vf") + 1]
