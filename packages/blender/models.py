from typing import Self

from pydantic import BaseModel, Field, model_validator


class Vector3(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Transform(BaseModel):
    location: Vector3 = Field(default_factory=Vector3)
    rotation_degrees: Vector3 = Field(default_factory=Vector3)
    scale: Vector3 = Field(default_factory=lambda: Vector3(x=1.0, y=1.0, z=1.0))


class RegistryCharacter(BaseModel):
    rig_object: str = Field(min_length=1, max_length=200)
    mouth_object: str = Field(default="", max_length=200)
    head_bone: str = Field(default="head", min_length=1, max_length=100)
    anchors: dict[str, str] = Field(default_factory=dict, max_length=100)
    actions: dict[str, str] = Field(default_factory=dict, max_length=100)
    default_anchor: str = Field(default="", max_length=100)


class BlenderSceneRegistry(BaseModel):
    version: int = Field(default=1, ge=1, le=10)
    scene_name: str = Field(min_length=2, max_length=200)
    characters: dict[str, RegistryCharacter] = Field(min_length=1, max_length=100)
    cameras: dict[str, str] = Field(min_length=1, max_length=100)
    props: dict[str, str] = Field(default_factory=dict, max_length=200)
    default_camera: str = Field(min_length=1, max_length=100)

    def character(self, name: str) -> RegistryCharacter:
        try:
            return self.characters[name]
        except KeyError as error:
            raise ValueError(f"Character '{name}' is not registered in the Blender scene") from error

    def camera_object(self, preset: str) -> str:
        key = preset if preset in self.cameras else self.default_camera
        try:
            return self.cameras[key]
        except KeyError as error:
            raise ValueError(f"Camera preset '{key}' is not registered in the Blender scene") from error


class VisemeCue(BaseModel):
    time_seconds: float = Field(ge=0)
    name: str = Field(min_length=1, max_length=50)
    weight: float = Field(default=1.0, ge=0, le=1)


class DialogueTrack(BaseModel):
    speaker: str = Field(min_length=1, max_length=200)
    text: str = Field(default="", max_length=4000)
    audio_path: str = Field(default="", max_length=2000)
    start_seconds: float = Field(default=0.0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0, le=60)
    visemes: list[VisemeCue] = Field(default_factory=list, max_length=5000)


class BlenderCharacterCue(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    rig_object: str = Field(min_length=1, max_length=200)
    mouth_object: str = Field(default="", max_length=200)
    head_bone: str = Field(default="head", min_length=1, max_length=100)
    anchor_object: str = Field(min_length=1, max_length=200)
    action_name: str = Field(default="", max_length=200)
    emotion: str = Field(default="neutral", max_length=100)
    look_at_object: str = Field(default="", max_length=200)
    transform_offset: Transform = Field(default_factory=Transform)
    dialogue: DialogueTrack | None = None


class PropCue(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    object_name: str = Field(min_length=1, max_length=200)
    visible: bool = True
    parent_character: str = Field(default="", max_length=200)
    parent_bone: str = Field(default="", max_length=100)
    transform: Transform = Field(default_factory=Transform)


class CameraCue(BaseModel):
    preset: str = Field(min_length=1, max_length=100)
    object_name: str = Field(min_length=1, max_length=200)
    look_at_object: str = Field(default="", max_length=200)
    movement: str = Field(default="locked", max_length=300)
    start_transform: Transform | None = None
    end_transform: Transform | None = None


class RenderSettings(BaseModel):
    width: int = Field(default=1280, ge=256, le=4096)
    height: int = Field(default=720, ge=256, le=4096)
    fps: int = Field(default=24, ge=4, le=60)
    duration_seconds: float = Field(default=4.0, ge=0.5, le=60)
    engine: str = Field(default="BLENDER_EEVEE_NEXT", min_length=2, max_length=100)
    samples: int = Field(default=32, ge=1, le=4096)
    transparent_background: bool = False

    @property
    def frame_end(self) -> int:
        return max(1, round(self.duration_seconds * self.fps))


class BlenderShotManifest(BaseModel):
    version: int = Field(default=1, ge=1, le=10)
    scene_number: int = Field(ge=1)
    shot_number: int = Field(ge=1)
    shot_key: str = Field(min_length=3, max_length=500)
    render: RenderSettings
    camera: CameraCue
    characters: list[BlenderCharacterCue] = Field(default_factory=list, max_length=20)
    props: list[PropCue] = Field(default_factory=list, max_length=100)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dialogue_window(self) -> Self:
        for character in self.characters:
            dialogue = character.dialogue
            if dialogue is None:
                continue
            if dialogue.start_seconds + dialogue.duration_seconds > self.render.duration_seconds + 0.001:
                raise ValueError(
                    f"Dialogue for {character.name} exceeds the Blender shot duration"
                )
            if dialogue.speaker != character.name:
                raise ValueError("Dialogue speaker must match its character cue")
        return self
