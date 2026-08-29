from typing import Literal

from pydantic import BaseModel, Field


class PromptPayload(BaseModel):
    prompt: str = Field(..., min_length=1)
    session_id: str = Field(default="default")
    system_instruction: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=2048, gt=0, le=8192)
    thinking_level: Literal["low", "medium", "high"] = "low"


class ResponsePayload(BaseModel):
    type: Literal["thought", "model_output", "tool_call", "tool_result"] = (Field(...),)
    content_type: Literal["text", "image", "function_call"] = (Field(default="text"),)
    content: str = Field(...)
