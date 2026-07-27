#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.blender.batch import build_episode_manifests
from packages.blender.models import BlenderSceneRegistry
from packages.direction.models import EpisodeDirection
from packages.scripts.models import EpisodeScript


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def plan(
    direction_path: Path,
    screenplay_path: Path,
    registry_path: Path,
    output_dir: Path,
    *,
    audio_root: Path | None,
    fps: int,
    width: int,
    height: int,
    samples: int,
) -> list[Path]:
    direction = EpisodeDirection.model_validate_json(direction_path.read_text(encoding="utf-8"))
    screenplay = EpisodeScript.model_validate_json(screenplay_path.read_text(encoding="utf-8"))
    registry = BlenderSceneRegistry.model_validate_json(registry_path.read_text(encoding="utf-8"))

    manifests = build_episode_manifests(
        direction,
        screenplay,
        registry,
        fps=fps,
        width=width,
        height=height,
        samples=samples,
        audio_root=audio_root,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("scene_*_shot_*.json"):
        stale.unlink()

    written: list[Path] = []
    index_items: list[dict[str, object]] = []
    for manifest in manifests:
        stem = f"scene_{manifest.scene_number:02d}_shot_{manifest.shot_number:02d}"
        path = output_dir / f"{stem}.json"
        path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        written.append(path)
        index_items.append(
            {
                "scene_number": manifest.scene_number,
                "shot_number": manifest.shot_number,
                "shot_key": manifest.shot_key,
                "duration_seconds": manifest.render.duration_seconds,
                "manifest": path.name,
                "output": f"{stem}.mp4",
            }
        )

    _write_json(
        output_dir / "sequence.json",
        {
            "version": 1,
            "episode_title": direction.title,
            "shot_count": len(index_items),
            "total_duration_seconds": sum(
                float(item["duration_seconds"]) for item in index_items
            ),
            "items": index_items,
        },
    )
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert an approved episode direction into Blender shot manifests."
    )
    parser.add_argument(
        "--direction",
        default="demo/first-real-episode/approved/direction.json",
    )
    parser.add_argument(
        "--screenplay",
        default="demo/first-real-episode/approved/screenplay.json",
    )
    parser.add_argument(
        "--registry",
        default="demo/first-real-episode/blender/scene_registry.json",
    )
    parser.add_argument("--output-dir", default="output/blender/manifests")
    parser.add_argument("--audio-root", default="")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--samples", type=int, default=32)
    args = parser.parse_args()

    try:
        paths = plan(
            Path(args.direction),
            Path(args.screenplay),
            Path(args.registry),
            Path(args.output_dir),
            audio_root=Path(args.audio_root) if args.audio_root else None,
            fps=args.fps,
            width=args.width,
            height=args.height,
            samples=args.samples,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"BLENDER_SEQUENCE_PLANNED={Path(args.output_dir).resolve()}")
    print(f"Shots: {len(paths)}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
