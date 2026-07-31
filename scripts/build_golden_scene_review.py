import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def _run(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _probe(path):
    result = _run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration,size",
        "-of", "json", str(path),
    ])
    return json.loads(result.stdout)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contact_sheet(video, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_graph = (
        "fps=1,scale=480:-1:flags=lanczos,"
        "drawtext=text='%{pts\\:hms}':x=12:y=h-th-12:fontsize=20:fontcolor=white:"
        "box=1:boxcolor=black@0.55,tile=4x2:padding=8:margin=8"
    )
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf", filter_graph, "-frames:v", "1", str(output)])


def _technical_checks(probe):
    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    duration = float(probe.get("format", {}).get("duration", 0.0))
    return {
        "video_stream_present": bool(video),
        "audio_stream_present": bool(audio),
        "resolution_1280x720": video.get("width") == 1280 and video.get("height") == 720,
        "duration_near_eight_seconds": abs(duration - 8.0) <= 0.12,
        "audio_sample_rate_48000": str(audio.get("sample_rate", "")) == "48000",
        "audio_channels_stereo": int(audio.get("channels", 0) or 0) == 2,
    }


def _report(video, contact_sheet, probe):
    checks = _technical_checks(probe)
    return {
        "status": "pending_human_review" if all(checks.values()) else "technical_failure",
        "production_approved": False,
        "promotion_blocked": True,
        "video": str(video.resolve()),
        "contact_sheet": str(contact_sheet.resolve()),
        "sha256": _sha256(video),
        "technical_checks": checks,
        "human_review": {
            "decision": "pending",
            "blocking_notes": [],
            "questions": [
                "Is the light failure clear without explanation?",
                "Do both characters visibly react to the same event?",
                "Are the characters appealing enough to continue watching?",
                "Does the scene remain alive between dialogue lines?",
                "Would an uninformed viewer voluntarily continue?",
            ],
        },
    }
