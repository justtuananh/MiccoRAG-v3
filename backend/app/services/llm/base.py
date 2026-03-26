from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMProvider(ABC):
    """Abstract provider contract for LLM integrations."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a full completion for a prompt."""

    @abstractmethod
    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        """Stream completion chunks for a prompt."""
