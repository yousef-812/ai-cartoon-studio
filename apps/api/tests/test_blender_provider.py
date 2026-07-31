import asyncio
import stat
from pathlib import Path

from packages.blender.provider import LocalBlenderVideoProvider
from packages.videos.models import VideoGenerationSpec


def _fake_blender(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env python3
import pathlib
import sys

if '--version' in sys.argv:
    print('Blender 4.x fake test runner')
    raise SystemExit(0)

output = pathlib.Path(sys.argv[sys.argv.index('--output') + 1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(b'fake-mp4')
print(f'BLENDER_SHOT_SUCCEEDED={output}')
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_local_blender_provider_runs_headless_job(tmp_path) -> None:
    binary = tmp_path / "fake_blender.py"
    _fake_blender(binary)
    runner = tmp_path / "runner.py"
    runner.write_text("print('runner')\n", encoding="utf-8")
    scene = tmp_path / "workshop.blend"
    scene.write_bytes(b"blend")

    provider = LocalBlenderVideoProvider(
        blender_binary=str(binary),
        runner_script=str(runner),
        jobs_path=str(tmp_path / "jobs"),
        timeout_seconds=10,
    )
    spec = VideoGenerationSpec(
        input_image_path=str(tmp_path / "environment.png"),
        input_scene_path=str(scene),
        prompt="Render a permanent workshop shot with two registered rigs.",
        duration_seconds=4,
        fps=24,
        metadata={
            "engine": "blender",
            "blender_manifest": {
                "version": 1,
                "scene_number": 1,
                "shot_number": 1,
                "shot_key": "scene:1:shot:1",
                "render": {
                    "width": 1280,
                    "height": 720,
                    "fps": 24,
                    "duration_seconds": 4,
                    "engine": "BLENDER_EEVEE_NEXT",
                    "samples": 16,
                },
                "camera": {
                    "preset": "wide",
                    "object_name": "CAM_Wide",
                },
                "characters": [],
            },
        },
    )

    health = asyncio.run(provider.health())
    submission = asyncio.run(provider.submit(spec))
    result = asyncio.run(provider.wait_for_result(submission.provider_job_id))

    assert health.available is True
    assert result.completed is True
    assert result.videos[0].storage_path.endswith("shot.mp4")
    assert Path(result.videos[0].storage_path).read_bytes() == b"fake-mp4"
    assert result.videos[0].metadata["engine"] == "blender"
