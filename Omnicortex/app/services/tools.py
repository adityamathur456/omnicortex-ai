from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class AgentTool(Generic[T]):
    name: str
    description: str
    run: Callable[[], Awaitable[T]]


class AgenticPipeline:
    async def execute(self, tools: list[AgentTool]) -> dict[str, object]:
        outputs: dict[str, object] = {}
        for tool in tools:
            outputs[tool.name] = await tool.run()
        return outputs


agentic_pipeline = AgenticPipeline()
