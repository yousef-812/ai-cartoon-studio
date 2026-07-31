import bpy

REQUIRED_OBJECTS = (
    "Omar_Rig",
    "Omar_Mouth",
    "Omar_Glasses_L",
    "Omar_Glasses_R",
    "Omar_Brow_L",
    "Omar_Brow_R",
    "Nader_Rig",
    "Nader_Mouth",
    "Nader_Hood",
    "Nader_Brow_L",
    "Nader_Brow_R",
    "CAM_Wide",
    "CAM_Medium",
    "CAM_Close",
    "ANCHOR_Omar_Left",
    "ANCHOR_Nader_Right",
    "ANCHOR_Window_Focus",
    "ANCHOR_Lantern_Focus",
    "PROP_Lantern",
    "PROP_Screwdriver",
    "FX_RainDrop_0",
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
    "Omar_ReactLightOut",
    "Omar_ConcernSettle",
    "Nader_Idle",
    "Nader_Talk",
    "Nader_Listen",
    "Nader_Point",
    "Nader_PickUp",
    "Nader_Walk",
    "Nader_Surprised",
    "Nader_Worried",
    "Nader_ReactLightOut",
    "Nader_ConcernSettle",
)


def _quality_failures():
    failures = []
    for index in range(6):
        rain = bpy.data.objects.get(f"FX_RainDrop_{index}")
        if rain is None:
            failures.append(f"missing rain drop {index}")
            continue
        if rain.hide_render:
            failures.append(f"rain drop {index} hidden from render")
        if rain.animation_data is None or rain.animation_data.action is None:
            failures.append(f"rain drop {index} has no animation")
    for name in ("Omar_Glasses_L", "Omar_Glasses_R", "Nader_Hood"):
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.parent_type != "BONE":
            failures.append(f"{name} is not bound to the character rig")
    return failures


def main() -> None:
    missing_objects = [name for name in REQUIRED_OBJECTS if bpy.data.objects.get(name) is None]
    missing_actions = [name for name in REQUIRED_ACTIONS if bpy.data.actions.get(name) is None]
    quality_failures = _quality_failures()
    print(f"Objects: {len(bpy.data.objects)}")
    print(f"Actions: {len(bpy.data.actions)}")
    print(f"Missing objects: {missing_objects}")
    print(f"Missing actions: {missing_actions}")
    print(f"Quality failures: {quality_failures}")
    if missing_objects or missing_actions or quality_failures:
        raise SystemExit("SCENE_VALIDATION_FAILED")
    print("BLENDER_SCENE_VALIDATION_SUCCEEDED")


if __name__ == "__main__":
    main()
