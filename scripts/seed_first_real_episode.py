#!/usr/bin/env python3
"""Seed the original one-minute Arabic demo episode into a running API.

The script is idempotent for the series, location, and character records. It creates
one new Story Job each time unless --skip-story is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "demo" / "first-real-episode"


def load_json(name: str) -> Any:
    return json.loads((DEMO_DIR / name).read_text(encoding="utf-8"))


def request_json(base_url: str, method: str, path: str, payload: Any | None = None) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310 - URL is operator supplied
            body = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach API at {base_url}: {error}") from error
    return json.loads(body) if body else None


def find_by(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    return next((item for item in items if item.get(key) == value), None)


def seed(base_url: str, *, skip_story: bool) -> dict[str, Any]:
    series_payload = load_json("series.json")
    characters_payload = load_json("characters.json")
    location_payload = load_json("location.json")
    episode_payload = load_json("episode_request.json")

    series_list = request_json(base_url, "GET", "/api/v1/series")
    series = find_by(series_list, "slug", series_payload["slug"])
    if series is None:
        series = request_json(base_url, "POST", "/api/v1/series", series_payload)
        print(f"Created series: {series['name']} ({series['id']})")
    else:
        print(f"Using existing series: {series['name']} ({series['id']})")
    series_id = series["id"]

    locations = request_json(base_url, "GET", f"/api/v1/series/{series_id}/locations")
    location = find_by(locations, "name", location_payload["name"])
    if location is None:
        location = request_json(
            base_url,
            "POST",
            f"/api/v1/series/{series_id}/locations",
            location_payload,
        )
        print(f"Created location: {location['name']}")
    else:
        print(f"Using existing location: {location['name']}")

    characters = request_json(base_url, "GET", f"/api/v1/series/{series_id}/characters")
    for character_payload in characters_payload:
        character = find_by(characters, "name", character_payload["name"])
        if character is None:
            character = request_json(
                base_url,
                "POST",
                f"/api/v1/series/{series_id}/characters",
                character_payload,
            )
            characters.append(character)
            print(f"Created character: {character['name']} ({character['id']})")
        else:
            print(f"Using existing character: {character['name']} ({character['id']})")

    story_job = None
    if not skip_story:
        story_job = request_json(
            base_url,
            "POST",
            f"/api/v1/series/{series_id}/story-jobs",
            episode_payload,
        )
        print(f"Queued Story Job: {story_job['id']} on {story_job['model']}")

    return {
        "series_id": series_id,
        "location_id": location["id"],
        "character_ids": {character["name"]: character["id"] for character in characters},
        "story_job_id": story_job["id"] if story_job else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument(
        "--skip-story",
        action="store_true",
        help="Only create the series bible, location, and characters.",
    )
    args = parser.parse_args()
    try:
        result = seed(args.api_url, skip_story=args.skip_story)
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("\nDemo source is ready:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\nOpen http://localhost:3000/production to review the Story Job.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
