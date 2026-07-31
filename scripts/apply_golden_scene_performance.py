import argparse
import json
from pathlib import Path


def _shift_dialogue(character, start_seconds):
    dialogue = character.get("dialogue")
    if not isinstance(dialogue, dict):
        return
    old_start = float(dialogue.get("start_seconds", 0.0))
    delta = start_seconds - old_start
    dialogue["start_seconds"] = start_seconds
    for cue in dialogue.get("visemes", []):
        cue["time_seconds"] = max(0.0, float(cue.get("time_seconds", 0.0)) + delta)


def _apply(path, actions, dialogue_start):
    data = json.loads(path.read_text(encoding="utf-8"))
    for character in data.get("characters", []):
        name = str(character.get("name", ""))
        action = actions.get(name)
        if action:
            character["action_name"] = action
        start = dialogue_start.get(name)
        if start is not None:
            _shift_dialogue(character, start)
    data.setdefault("metadata", {})["golden_scene_performance_override"] = True
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GOLDEN_SCENE_PERFORMANCE_APPLIED={path.name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-dir", default="output/blender/manifests")
    args = parser.parse_args()
    root = Path(args.manifest_dir)
    shot1 = root / "scene_01_shot_01.json"
    shot2 = root / "scene_01_shot_02.json"
    if not shot1.is_file() or not shot2.is_file():
        raise SystemExit("Golden Scene manifests are missing")
    _apply(
        shot1,
        {"عمر": "Omar_ReactLightOut", "نادر": "Nader_Surprised"},
        {"عمر": 0.82},
    )
    _apply(
        shot2,
        {"نادر": "Nader_Worried"},
        {"نادر": 1.42},
    )


if __name__ == "__main__":
    main()
