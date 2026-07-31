from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CharacterRecord
from packages.characters.models import CharacterCreate, CharacterRead, CharacterUpdate


class SQLCharacterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: CharacterRecord) -> CharacterRead:
        return CharacterRead.model_validate(record)

    def create(self, series_id: str, payload: CharacterCreate) -> CharacterRead:
        record = CharacterRecord(
            series_id=series_id,
            name=payload.name,
            role=payload.role.value,
            age_range=payload.age_range,
            description=payload.description,
            personality_traits=payload.personality_traits,
            visual_identity=payload.visual_identity.model_dump(mode="json"),
            wardrobe=payload.wardrobe,
            speaking_style=payload.speaking_style,
            voice_profile=payload.voice_profile.model_dump(mode="json"),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def list_for_series(self, series_id: str) -> list[CharacterRead]:
        records = self.session.scalars(
            select(CharacterRecord)
            .where(CharacterRecord.series_id == series_id)
            .order_by(CharacterRecord.created_at)
        ).all()
        return [self._to_read(record) for record in records]

    def get(self, character_id: str) -> CharacterRead | None:
        record = self.session.get(CharacterRecord, character_id)
        return self._to_read(record) if record is not None else None

    def update(self, character_id: str, payload: CharacterUpdate) -> CharacterRead | None:
        record = self.session.get(CharacterRecord, character_id)
        if record is None:
            return None

        changes = payload.model_dump(exclude_unset=True, mode="json")
        for field, value in changes.items():
            if field == "role" and value is not None:
                value = str(value)
            setattr(record, field, value)
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def name_exists(self, series_id: str, name: str, exclude_id: str | None = None) -> bool:
        statement = select(CharacterRecord.id).where(
            CharacterRecord.series_id == series_id,
            func.lower(CharacterRecord.name) == name.strip().lower(),
        )
        if exclude_id is not None:
            statement = statement.where(CharacterRecord.id != exclude_id)
        return self.session.scalar(statement.limit(1)) is not None
