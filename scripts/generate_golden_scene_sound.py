import argparse
import math
import random
import struct
import wave
from pathlib import Path

RATE = 48000


def _write(path, samples):
    peak = max(1e-6, max(abs(value) for value in samples))
    scale = 0.92 / peak
    frames = b"".join(struct.pack("<h", int(max(-1, min(1, value * scale)) * 32767)) for value in samples)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(frames)


def _rain(seconds):
    rng = random.Random(812)
    total = int(seconds * RATE)
    state = 0.0
    result = []
    for index in range(total):
        white = rng.uniform(-1, 1)
        state = (0.985 * state) + (0.015 * white)
        hiss = white * 0.16
        rumble = math.sin(2 * math.pi * 72 * index / RATE) * 0.018
        result.append((state * 0.55) + hiss + rumble)
    return result


def _flicker(seconds):
    total = int(seconds * RATE)
    result = []
    for index in range(total):
        t = index / RATE
        envelope = math.exp(-3.2 * t)
        buzz = math.sin(2 * math.pi * 118 * t) + (0.45 * math.sin(2 * math.pi * 236 * t))
        clicks = 0.8 if any(abs(t - mark) < 0.006 for mark in (0.05, 0.22, 0.47, 0.75)) else 0.0
        result.append((buzz * 0.11 * envelope) + clicks)
    return result


def _thunder(seconds):
    rng = random.Random(2026)
    total = int(seconds * RATE)
    result = []
    low = 0.0
    for index in range(total):
        t = index / RATE
        noise = rng.uniform(-1, 1)
        low = (0.995 * low) + (0.005 * noise)
        attack = min(1.0, t / 0.035)
        decay = math.exp(-1.7 * t)
        body = math.sin(2 * math.pi * (48 + (9 * math.sin(t * 4))) * t)
        result.append((low * 1.3 + body * 0.35) * attack * decay)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output/golden-scene/sound")
    args = parser.parse_args()
    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "rain.wav": _rain(8.2),
        "flicker.wav": _flicker(1.1),
        "thunder.wav": _thunder(2.3),
    }
    for name, samples in outputs.items():
        path = root / name
        _write(path, samples)
        print(f"GOLDEN_SOUND_READY={path.resolve()}")


if __name__ == "__main__":
    main()
