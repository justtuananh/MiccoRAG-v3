from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLMProvider interface."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = "gpt-4o-mini"

    async def generate(self, prompt: str) -> str:
        response = await self._client.responses.create(model=self._model, input=prompt)
        return getattr(response, "output_text", "")

    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        stream = await self._client.responses.create(model=self._model, input=prompt, stream=True)
        async for event in stream:
            delta = getattr(event, "delta", None)
            if delta:
                yield str(delta)
