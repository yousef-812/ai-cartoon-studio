from typing import Literal

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class LLMHealth(BaseModel):
    available: bool
    provider: str
    model: str
    detail: str = ""
