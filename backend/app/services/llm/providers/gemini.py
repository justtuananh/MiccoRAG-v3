from collections.abc import AsyncIterator

import google.generativeai as genai

from app.core.config import get_settings
from app.services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Gemini implementation of the LLMProvider interface."""

    def __init__(self) -> None:
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate(self, prompt: str) -> str:
        response = await self._model.generate_content_async(prompt)
        return getattr(response, "text", "")

    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        response = await self._model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield str(text)
