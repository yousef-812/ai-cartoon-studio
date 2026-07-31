from packages.characters.models import CharacterCreate, CharacterRead, CharacterUpdate
from packages.characters.repository import CharacterRepository
from packages.common.errors import ConflictError, NotFoundError


class CharacterService:
    def __init__(self, repository: CharacterRepository) -> None:
        self.repository = repository

    def create(self, series_id: str, payload: CharacterCreate) -> CharacterRead:
        if self.repository.name_exists(series_id, payload.name):
            raise ConflictError(f"Character '{payload.name}' already exists in this series")
        return self.repository.create(series_id, payload)

    def list_for_series(self, series_id: str) -> list[CharacterRead]:
        return self.repository.list_for_series(series_id)

    def get(self, character_id: str) -> CharacterRead:
        character = self.repository.get(character_id)
        if character is None:
            raise NotFoundError("Character not found")
        return character

    def update(self, character_id: str, payload: CharacterUpdate) -> CharacterRead:
        current = self.get(character_id)
        if payload.name is not None and self.repository.name_exists(
            current.series_id, payload.name, exclude_id=character_id
        ):
            raise ConflictError(f"Character '{payload.name}' already exists in this series")

        character = self.repository.update(character_id, payload)
        if character is None:
            raise NotFoundError("Character not found")
        return character
