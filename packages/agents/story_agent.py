from typing import Any

from packages.agents.base import ProductionAgent


class StoryAgent(ProductionAgent):
    name = "story"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Connect an LLM provider through the provider registry.")
