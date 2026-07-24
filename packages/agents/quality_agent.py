from typing import Any

from packages.agents.base import ProductionAgent


class QualityAgent(ProductionAgent):
    name = "quality"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Multimodal quality checks are pending.")
