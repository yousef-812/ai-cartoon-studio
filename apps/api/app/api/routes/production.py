from fastapi import APIRouter, HTTPException, status
from packages.pipeline.models import EpisodeRequest, EpisodeState
from packages.pipeline.orchestrator import EpisodeOrchestrator

router = APIRouter()
orchestrator = EpisodeOrchestrator()


@router.post("/episodes", response_model=EpisodeState, status_code=status.HTTP_202_ACCEPTED)
def create_episode(request: EpisodeRequest) -> EpisodeState:
    return orchestrator.create_episode(request)


@router.get("/episodes/{episode_id}", response_model=EpisodeState)
def get_episode(episode_id: str) -> EpisodeState:
    episode = orchestrator.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode
