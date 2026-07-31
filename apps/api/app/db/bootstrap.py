from app.db.base import Base
from app.db.session import engine


def initialize_database() -> None:
    from app.db import asset_models, finalization_models, models, sound_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
