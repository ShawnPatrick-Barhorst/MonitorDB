import os
from typing import Any, Literal

from google import genai
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


class GeminiEngine:
    def __init__(
        self, api_key: str | None = None, default_model: str = "gemini-3.5-flash"
    ):

        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("No API key provided.")
        self.client = genai.Client(api_key=api_key)
        self.model = default_model
        self.sessions: dict[str, Any] = {}

    def _retrieve_or_create_session(
        self,
        session_id: str,
    ):

        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            self.sessions[session_id] = []
            return self.sessions[session_id]

    def step_interaction(self, payload: PromptPayload) -> str:

        session_history = self._retrieve_or_create_session(payload.session_id)

        message = {
            "type": "user_input",
            "content": [{"type": "text", "text": payload.prompt}],
        }
        session_history.append(message)

        generation_config = {
            "temperature": payload.temperature,
            "max_output_tokens": payload.max_output_tokens,
            "thinking_level": payload.thinking_level,
        }

        interaction = self.client.interactions.create(
            model=self.model,
            store=False,
            input=session_history,
            generation_config=generation_config,
        )

        final_text = ""
        thought_text = ""
        for step in interaction.steps:
            session_history.append(step.model_dump())
            if step.type == "thought":
                # ThoughtStep uses .summary (if present)
                if hasattr(step, "summary") and step.summary:
                    for block in step.summary:
                        thought_text += getattr(block, "text", "")

            elif step.type == "model_output" and (
                hasattr(step, "content") and step.content
            ):
                # ModelOutputStep contains .content and .id
                # if hasattr(step, "content") and step.content:
                for block in step.content:
                    final_text += getattr(block, "text", "")

        response = ResponsePayload(
            type="model_output",
            content_type="text",
            content=final_text,
        )

        return response

    def chat(
        self,
        prompt: str,
        session_id: str = "default",
        *,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        thinking_level: Literal["low", "medium", "high"],
        system_instruction: str | None = None,
    ):

        PromptPayload(
            prompt=prompt,
            session_id=session_id,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
            system_instruction=system_instruction,
        )

        Response = self.step_interaction(PromptPayload)

        return Response
