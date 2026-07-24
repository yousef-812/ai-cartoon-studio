from typing import Any

from packages.agents.base import ProductionAgent


class DirectorAgent(ProductionAgent):
    name = "director"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Shot planning implementation is pending.")
