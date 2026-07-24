from abc import ABC, abstractmethod
from typing import Any


class ProductionAgent(ABC):
    name: str

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run one production reasoning stage and return structured output."""
