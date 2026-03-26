from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.openai import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    """Return configured LLM provider based on LLM_PROVIDER env var."""
    provider = get_settings().llm_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    return OpenAIProvider()
