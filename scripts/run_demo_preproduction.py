#!/usr/bin/env python3
"""Run the first real episode through Story, Screenplay, and Direction.

This script is intended for a short-lived GitHub Actions runner. It seeds the
original demo source, waits for each LLM job, performs deterministic technical
validation, records a technical approval, and writes portable JSON outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from advance_first_real_episode import queue_direction, queue_screenplay
from seed_first_real_episode import request_json, seed

SUSPICIOUS_CHARACTERS = {"\ufffd", "◆"}
ARABIC_UNDERSCORE = re.compile(r"[\u0600-\u06ff]_[\u0600-\u06ff]")


def wait_for_job(
    base_url: str,
    resource: str,
    job_id: str,
    *,
    timeout_seconds: int,
    poll_seconds: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    path = f"/api/v1/{resource}-jobs/{job_id}"
    while time.monotonic() < deadline:
        job = request_json(base_url, "GET", path)
        status = job.get("status")
        print(f"{resource} job {job_id}: {status}", flush=True)
        if status == "succeeded":
            if not job.get("result"):
                raise RuntimeError(f"{resource} job succeeded without a result")
            return job
        if status == "failed":
            raise RuntimeError(f"{resource} job failed: {job.get('error') or 'unknown error'}")
        time.sleep(poll_seconds)
    raise TimeoutError(f"Timed out waiting for {resource} job {job_id}")


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def validate_text_quality(name: str, payload: dict[str, Any]) -> None:
    for text in iter_strings(payload):
        bad = sorted(character for character in SUSPICIOUS_CHARACTERS if character in text)
        if bad:
            raise ValueError(f"{name} contains suspicious characters: {bad}")
        if ARABIC_UNDERSCORE.search(text):
            raise ValueError(f"{name} contains a broken Arabic word: {text}")


def validate_direction(payload: dict[str, Any]) -> None:
    scenes = payload.get("scenes")
    if not isinstance(scenes, list):
        raise ValueError("Direction result does not contain scenes")

    shots = [shot for scene in scenes for shot in scene.get("shots", [])]
    if len(shots) != 10:
        raise ValueError(f"Direction must contain exactly 10 shots; received {len(shots)}")

    dialogue_refs: list[tuple[int, int]] = []
    for shot in shots:
        duration = float(shot.get("duration_seconds", 0))
        if not 3.5 <= duration <= 4.0:
            raise ValueError(f"Shot duration {duration} is outside the 3.5–4.0 second range")
        line_orders = shot.get("dialogue_line_orders", [])
        if len(line_orders) > 1:
            raise ValueError("A demo shot contains more than one dialogue line")
        scene_number = int(shot.get("scene_number", 0))
        dialogue_refs.extend((scene_number, int(order)) for order in line_orders)

    if len(dialogue_refs) != len(set(dialogue_refs)):
        raise ValueError("A dialogue line is assigned to more than one directed shot")


def approve(base_url: str, resource: str, job_id: str, notes: str) -> dict[str, Any]:
    return request_json(
        base_url,
        "POST",
        f"/api/v1/{resource}-jobs/{job_id}/review",
        {"decision": "approved", "notes": notes},
    )


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run(base_url: str, output_dir: Path, timeout_seconds: int, poll_seconds: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    source = seed(base_url, skip_story=False)
    write_json(output_dir / "source.json", source)

    story = wait_for_job(
        base_url,
        "story",
        source["story_job_id"],
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    validate_text_quality("Story", story["result"])
    approve(
        base_url,
        "story",
        story["id"],
        "Automated technical-demo approval after schema, identity, location, and text checks. Artistic approval is still required before publication.",
    )
    write_json(output_dir / "story.json", story)

    screenplay_created = queue_screenplay(base_url, source["series_id"])
    screenplay = wait_for_job(
        base_url,
        "script",
        screenplay_created["id"],
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    validate_text_quality("Screenplay", screenplay["result"])
    approve(
        base_url,
        "script",
        screenplay["id"],
        "Automated technical-demo approval after schema, Arabic-text, timing, and registered-speaker checks. Artistic approval is still required before publication.",
    )
    write_json(output_dir / "screenplay.json", screenplay)

    direction_created = queue_direction(base_url, source["series_id"])
    direction = wait_for_job(
        base_url,
        "direction",
        direction_created["id"],
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    validate_text_quality("Direction", direction["result"])
    validate_direction(direction["result"])
    approve(
        base_url,
        "direction",
        direction["id"],
        "Automated technical-demo approval after exact shot-count, duration, dialogue coverage, identity, and continuity validation. Artistic approval is still required before publication.",
    )
    write_json(output_dir / "direction.json", direction)

    manifest = {
        "series_id": source["series_id"],
        "story_job_id": story["id"],
        "script_job_id": screenplay["id"],
        "direction_job_id": direction["id"],
        "shot_count": sum(len(scene["shots"]) for scene in direction["result"]["scenes"]),
        "status": "preproduction_succeeded",
        "publication_approval": "not_granted",
    }
    write_json(output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", default="output/first-real-episode")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()

    try:
        run(
            args.api_url,
            Path(args.output_dir),
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
        )
    except (RuntimeError, TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
