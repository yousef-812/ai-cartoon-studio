#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.blender.preview import build_preview


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and concatenate rendered Blender shots into a silent preview."
    )
    parser.add_argument(
        "--sequence",
        default="output/blender/manifests/sequence.json",
    )
    parser.add_argument(
        "--rendered-dir",
        default="output/blender/sequence",
    )
    parser.add_argument(
        "--output",
        default="output/blender/sequence_preview.mp4",
    )
    parser.add_argument(
        "--report",
        default="output/blender/sequence_preview_report.json",
    )
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--ffmpeg-binary", default="ffmpeg")
    parser.add_argument("--ffprobe-binary", default="ffprobe")
    args = parser.parse_args()

    try:
        report = build_preview(
            Path(args.sequence),
            Path(args.rendered_dir),
            Path(args.output),
            Path(args.report),
            limit=args.limit,
            ffmpeg_binary=args.ffmpeg_binary,
            ffprobe_binary=args.ffprobe_binary,
        )
    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"BLENDER_PREVIEW_SUCCEEDED={Path(args.output).resolve()}")
    print(f"BLENDER_PREVIEW_REPORT={Path(args.report).resolve()}")
    print(f"Selected shots: {report['selected_shots']}")
    print(f"Expected duration: {report['expected_duration_seconds']:.3f}s")
    print(f"Actual duration: {report['preview_probe']['duration_seconds']:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
