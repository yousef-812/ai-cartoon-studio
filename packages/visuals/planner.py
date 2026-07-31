from packages.characters.models import CharacterRead
from packages.direction.models import EpisodeDirection
from packages.images.models import ImageGenerationSpec
from packages.series.models import LocationRead, SeriesRead
from packages.visuals.models import VisualAssetSpec, VisualAssetType


class VisualAssetPlanner:
    def plan(
        self,
        series: SeriesRead,
        characters: list[CharacterRead],
        locations: list[LocationRead],
        direction: EpisodeDirection,
    ) -> list[VisualAssetSpec]:
        character_map = {character.name: character for character in characters}
        location_map = {location.name: location for location in locations}
        used_characters = sorted(
            {
                name
                for scene in direction.scenes
                for shot in scene.shots
                for name in shot.characters
            }
        )
        used_locations = sorted(
            {shot.location for scene in direction.scenes for shot in scene.shots}
        )

        specs: list[VisualAssetSpec] = []
        for name in used_characters:
            character = character_map[name]
            reference_key = self.character_reference_key(name)
            specs.append(
                VisualAssetSpec(
                    key=reference_key,
                    asset_type=VisualAssetType.CHARACTER_REFERENCE,
                    name=f"{name} permanent character reference",
                    character_name=name,
                    generation=ImageGenerationSpec(
                        prompt=self._character_prompt(series, character),
                        negative_prompt=self._negative_prompt(),
                        width=1024,
                        height=1024,
                        metadata={"character_name": name, "purpose": "permanent_reference"},
                    ),
                )
            )
            specs.append(
                VisualAssetSpec(
                    key=f"character:{name}:expressions",
                    asset_type=VisualAssetType.CHARACTER_EXPRESSION_SHEET,
                    name=f"{name} expression sheet",
                    character_name=name,
                    dependency_keys=[reference_key],
                    generation=ImageGenerationSpec(
                        prompt=(
                            f"Expression sheet for the exact same character: "
                            f"{character.visual_identity.reference_prompt}. Show neutral, joy, "
                            "sadness, fear, anger, surprise, determination, and relief. "
                            f"Use {series.visual_style.art_direction}. Clean production turnaround."
                        ),
                        negative_prompt=self._negative_prompt(),
                        width=1536,
                        height=1024,
                        metadata={"character_name": name, "purpose": "expressions"},
                    ),
                )
            )

        for location_name in used_locations:
            location = location_map.get(location_name)
            prompt = (
                location.visual_prompt
                if location is not None
                else f"Production background for {location_name}"
            )
            specs.append(
                VisualAssetSpec(
                    key=self.background_key(location_name),
                    asset_type=VisualAssetType.BACKGROUND,
                    name=f"{location_name} master background",
                    location_name=location_name,
                    generation=ImageGenerationSpec(
                        prompt=(
                            f"{prompt}. {series.visual_style.art_direction}. "
                            "Wide clean animation background, no characters, reusable layout, "
                            f"{series.visual_style.lighting}, {series.visual_style.aspect_ratio}."
                        ),
                        negative_prompt=(
                            "people, characters, text, watermark, logo, distorted perspective, "
                            "photorealism, inconsistent architecture"
                        ),
                        width=1280,
                        height=720,
                        metadata={"location_name": location_name, "purpose": "master_background"},
                    ),
                )
            )

        for scene in direction.scenes:
            for shot in scene.shots:
                dependencies = [self.background_key(shot.location)]
                dependencies.extend(self.character_reference_key(name) for name in shot.characters)
                specs.append(
                    VisualAssetSpec(
                        key=f"shot:{scene.scene_number}:{shot.number}:keyframe",
                        asset_type=VisualAssetType.SHOT_KEYFRAME,
                        name=f"Scene {scene.scene_number} shot {shot.number} keyframe",
                        scene_number=scene.scene_number,
                        shot_number=shot.number,
                        location_name=shot.location,
                        dependency_keys=dependencies,
                        generation=ImageGenerationSpec(
                            prompt=(
                                f"{shot.visual_prompt}. Shot size: {shot.shot_size}. "
                                f"Camera angle: {shot.camera_angle}. Composition: {shot.composition}. "
                                f"Visible action: {shot.action}. Emotion: {shot.emotion}. "
                                f"{series.visual_style.art_direction}. "
                                "Production keyframe, stable character identity, clean anatomy, "
                                "clear silhouettes, no subtitles or text."
                            ),
                            negative_prompt=self._negative_prompt(),
                            width=1280,
                            height=720,
                            metadata={
                                "scene_number": scene.scene_number,
                                "shot_number": shot.number,
                                "characters": shot.characters,
                                "location": shot.location,
                                "purpose": "shot_keyframe",
                            },
                        ),
                    )
                )
        return specs

    @staticmethod
    def character_reference_key(name: str) -> str:
        return f"character:{name}:reference"

    @staticmethod
    def background_key(name: str) -> str:
        return f"location:{name}:background"

    @staticmethod
    def _negative_prompt() -> str:
        return (
            "text, watermark, logo, signature, extra limbs, missing fingers, duplicate character, "
            "deformed face, inconsistent costume, inconsistent colors, photorealism, low detail"
        )

    @staticmethod
    def _character_prompt(series: SeriesRead, character: CharacterRead) -> str:
        identity = character.visual_identity
        wardrobe = ", ".join(f"{key}: {value}" for key, value in character.wardrobe.items())
        features = ", ".join(identity.signature_features)
        palette = ", ".join(identity.palette)
        return (
            f"Permanent animation character reference sheet for {character.name}. "
            f"{identity.reference_prompt}. Body: {identity.body_shape}. Face: {identity.face}. "
            f"Hair: {identity.hair}. Signature features: {features}. Wardrobe: {wardrobe}. "
            f"Palette: {palette}. {series.visual_style.art_direction}. "
            "Front, three-quarter, side, and back views; neutral pose; consistent proportions; "
            "plain background; no text; production model sheet."
        )
