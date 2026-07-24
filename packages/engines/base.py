from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GenerationResult:
    artifact_path: Path
    provider: str
    model: str
    cost_usd: float
    metadata: dict[str, Any]


class MediaEngine(ABC):
    capability: str

    @abstractmethod
    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        """Generate one reviewable media artifact."""
