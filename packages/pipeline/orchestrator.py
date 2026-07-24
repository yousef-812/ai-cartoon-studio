from threading import Lock

from packages.pipeline.models import EpisodeRequest, EpisodeState


class EpisodeOrchestrator:
    """Temporary in-memory control plane; persistence and workers plug in here."""

    def __init__(self) -> None:
        self._episodes: dict[str, EpisodeState] = {}
        self._lock = Lock()

    def create_episode(self, request: EpisodeRequest) -> EpisodeState:
        episode = EpisodeState(**request.model_dump())
        with self._lock:
            self._episodes[episode.id] = episode
        return episode

    def get_episode(self, episode_id: str) -> EpisodeState | None:
        return self._episodes.get(episode_id)
