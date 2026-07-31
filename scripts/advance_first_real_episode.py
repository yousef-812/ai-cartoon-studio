#!/usr/bin/env python3
"""Queue the constrained screenplay or direction job for the first real episode."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SERIES_SLUG = "workshop-of-light-demo"


def request_json(base_url: str, method: str, path: str, payload: Any | None = None) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310 - operator supplied API
            body = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach API: {error}") from error
    return json.loads(body) if body else None


def approved_job(jobs: list[dict[str, Any]], name: str) -> dict[str, Any]:
    job = next(
        (
            item
            for item in jobs
            if item.get("status") == "succeeded"
            and item.get("review_status") == "approved"
            and item.get("result")
        ),
        None,
    )
    if job is None:
        raise RuntimeError(f"No approved successful {name} job was found")
    return job


def series_id(base_url: str) -> str:
    series = request_json(base_url, "GET", "/api/v1/series")
    match = next((item for item in series if item.get("slug") == SERIES_SLUG), None)
    if match is None:
        raise RuntimeError("Run scripts/seed_first_real_episode.py first")
    return str(match["id"])


def queue_screenplay(base_url: str, demo_series_id: str) -> dict[str, Any]:
    story = approved_job(
        request_json(base_url, "GET", f"/api/v1/series/{demo_series_id}/story-jobs"),
        "story",
    )
    payload = {
        "target_duration_seconds": 40,
        "dialogue_style": "clear Modern Standard Arabic, concise, character-specific, and lip-sync friendly",
        "pacing": "ten short visual beats with fast escalation and a warm clean resolution",
        "constraints": [
            "Use only عمر and نادر as exact speaker names.",
            "Use only the approved main workshop location.",
            "Keep every spoken sentence short enough for a four-second shot.",
            "Never write overlapping dialogue.",
            "Do not make both characters speak at the same moment.",
            "Keep the total screenplay close to 40 seconds.",
            "Preserve the four required emergency-lamp story beats.",
        ],
    }
    return request_json(
        base_url,
        "POST",
        f"/api/v1/story-jobs/{story['id']}/script-jobs",
        payload,
    )


def queue_direction(base_url: str, demo_series_id: str) -> dict[str, Any]:
    screenplay = approved_job(
        request_json(base_url, "GET", f"/api/v1/series/{demo_series_id}/script-jobs"),
        "screenplay",
    )
    payload = {
        "min_shot_duration_seconds": 3.5,
        "max_shot_duration_seconds": 4.0,
        "target_shot_count": 10,
        "max_dialogue_lines_per_shot": 1,
        "directing_style": "cinematic stylized 3D animation, readable faces, minimal motion, free-GPU efficient",
        "constraints": [
            "Create exactly 10 shots across all scenes.",
            "Keep every shot between 3.5 and 4.0 seconds.",
            "Assign at most one speaking character to each shot.",
            "Place each dialogue line order in exactly one shot.",
            "Use front or three-quarter faces for speaking shots.",
            "Avoid complex hand close-ups and rapid camera motion.",
            "Keep the storm window camera-left and the workbench centered.",
            "Preserve Omar's teal jacket and glasses and Nader's orange hoodie and navy apron.",
            "End on the warm emergency lamp lighting both faces.",
        ],
    }
    return request_json(
        base_url,
        "POST",
        f"/api/v1/script-jobs/{screenplay['id']}/direction-jobs",
        payload,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("screenplay", "direction"))
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()
    try:
        demo_series_id = series_id(args.api_url)
        job = (
            queue_screenplay(args.api_url, demo_series_id)
            if args.stage == "screenplay"
            else queue_direction(args.api_url, demo_series_id)
        )
    except (RuntimeError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(job, ensure_ascii=False, indent=2))
    print(f"Queued constrained {args.stage} job: {job['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
