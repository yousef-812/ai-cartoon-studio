from packages.characters.models import CharacterRead


def build_consistency_prompt(character: CharacterRead) -> str:
    identity = character.visual_identity
    features = ", ".join(identity.signature_features) or "no additional signature features"
    palette = ", ".join(identity.palette) or "series palette"
    return (
        f"Character identity lock: {character.name}. "
        f"{identity.reference_prompt}. Body: {identity.body_shape or 'use reference'}. "
        f"Face: {identity.face or 'use reference'}. Hair: {identity.hair or 'use reference'}. "
        f"Palette: {palette}. Signature features: {features}. "
        "Preserve facial proportions, body proportions, wardrobe identity, and color placement."
    )
