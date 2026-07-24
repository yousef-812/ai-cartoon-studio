from typing import Any

from packages.agents.base import ProductionAgent


class ContinuityAgent(ProductionAgent):
    name = "continuity"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Series and character continuity checks are pending.")
