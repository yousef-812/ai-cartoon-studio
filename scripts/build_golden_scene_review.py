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
