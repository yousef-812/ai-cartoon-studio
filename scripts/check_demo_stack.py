#!/usr/bin/env python3
"""Check every provider required by the first real episode before generation starts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def host_url(value: str) -> str:
    return (
        value.rstrip("/")
        .replace("host.docker.internal", "localhost")
        .replace("piper-tts:8001", "localhost:8001")
        .replace("procedural-sound:8002", "localhost:8002")
    )


def endpoint(base_url: str, path: str) -> str:
    if path.startswith("/v1/") and base_url.endswith("/v1"):
        return f"{base_url}{path[3:]}"
    return f"{base_url}{path}"


def fetch_json(url: str, api_key: str = "") -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=25) as response:  # noqa: S310 - configured local endpoints
            payload = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {detail[:500]}") from error
    except URLError as error:
        raise RuntimeError(str(error)) from error
    if not payload:
        return {}
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise RuntimeError("Endpoint did not return a JSON object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=str(ROOT / ".env"))
    args = parser.parse_args()
    load_env(Path(args.env_file))

    api_url = host_url(os.getenv("DEMO_API_URL", "http://localhost:8000"))
    llm_url = host_url(os.getenv("DEMO_LLM_URL", os.getenv("LLM_BASE_URL", "")))
    comfy_url = host_url(os.getenv("DEMO_COMFY_URL", os.getenv("IMAGE_BASE_URL", "")))
    voice_url = host_url(os.getenv("DEMO_VOICE_URL", os.getenv("VOICE_BASE_URL", "http://localhost:8001")))
    lip_url = host_url(os.getenv("DEMO_LIP_SYNC_URL", os.getenv("LIP_SYNC_BASE_URL", "")))
    sound_url = host_url(os.getenv("DEMO_SOUND_URL", os.getenv("SOUND_BASE_URL", "http://localhost:8002")))

    checks = [
        ("API", endpoint(api_url, "/api/v1/health"), ""),
        ("Qwen LLM", endpoint(llm_url, "/v1/models") if llm_url else "", os.getenv("LLM_API_KEY", "")),
        ("ComfyUI", endpoint(comfy_url, "/system_stats") if comfy_url else "", ""),
        ("Piper TTS", endpoint(voice_url, "/health"), ""),
        ("MuseTalk", endpoint(lip_url, "/health") if lip_url else "", os.getenv("LIP_SYNC_API_KEY", "")),
        ("Procedural sound", endpoint(sound_url, "/health"), ""),
        ("Finalization", endpoint(api_url, "/api/v1/finalization/health"), ""),
    ]

    failed = False
    print("First real episode provider preflight\n")
    for name, url, api_key in checks:
        if not url:
            print(f"[FAIL] {name:<20} URL is not configured")
            failed = True
            continue
        try:
            payload = fetch_json(url, api_key)
            available = payload.get("available", True)
            detail = payload.get("detail") or payload.get("status") or "reachable"
            if available is False:
                raise RuntimeError(str(detail))
            print(f"[ OK ] {name:<20} {detail}")
        except (RuntimeError, ValueError, json.JSONDecodeError) as error:
            print(f"[FAIL] {name:<20} {error}")
            failed = True

    if failed:
        print("\nDo not seed or generate the episode until every line is [ OK ].", file=sys.stderr)
        return 1
    print("\nAll providers are ready. Seed the demo episode now.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
