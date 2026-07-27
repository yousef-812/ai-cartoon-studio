import bpy


REQUIRED_OBJECTS = (
    "Omar_Rig",
    "Omar_Mouth",
    "Nader_Rig",
    "Nader_Mouth",
    "CAM_Wide",
    "CAM_Medium",
    "CAM_Close",
    "ANCHOR_Omar_Left",
    "ANCHOR_Nader_Right",
    "PROP_Lantern",
    "PROP_Screwdriver",
)

REQUIRED_ACTIONS = (
    "Omar_Idle",
    "Omar_Talk",
    "Omar_Listen",
    "Omar_Point",
    "Omar_PickUp",
    "Omar_Walk",
    "Omar_Surprised",
    "Omar_Worried",
    "Nader_Idle",
    "Nader_Talk",
    "Nader_Listen",
    "Nader_Point",
    "Nader_PickUp",
    "Nader_Walk",
    "Nader_Surprised",
    "Nader_Worried",
)


def main() -> None:
    missing_objects = [name for name in REQUIRED_OBJECTS if bpy.data.objects.get(name) is None]
    missing_actions = [name for name in REQUIRED_ACTIONS if bpy.data.actions.get(name) is None]

    print(f"Objects: {len(bpy.data.objects)}")
    print(f"Actions: {len(bpy.data.actions)}")
    print(f"Missing objects: {missing_objects}")
    print(f"Missing actions: {missing_actions}")

    if missing_objects or missing_actions:
        raise SystemExit("SCENE_VALIDATION_FAILED")

    print("BLENDER_SCENE_VALIDATION_SUCCEEDED")


if __name__ == "__main__":
    main()
