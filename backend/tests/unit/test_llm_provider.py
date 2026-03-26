from types import SimpleNamespace

import pytest

from app.services.llm import get_llm_provider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.openai import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_generate_returns_output_text(mocker):
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider._client = mocker.Mock()
    provider._model = "gpt-4o-mini"
    provider._client.responses.create = mocker.AsyncMock(
        return_value=SimpleNamespace(output_text="hello from openai")
    )

    result = await OpenAIProvider.generate(provider, "hello")

    assert result == "hello from openai"


@pytest.mark.asyncio
async def test_gemini_provider_generate_returns_text(mocker):
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._model = mocker.Mock()
    provider._model.generate_content_async = mocker.AsyncMock(
        return_value=SimpleNamespace(text="hello from gemini")
    )

    result = await GeminiProvider.generate(provider, "hello")

    assert result == "hello from gemini"


def test_get_llm_provider_with_gemini_setting_returns_gemini(mocker):
    mocker.patch("app.services.llm.get_settings", return_value=SimpleNamespace(llm_provider="gemini"))

    provider = get_llm_provider()

    assert isinstance(provider, GeminiProvider)


def test_get_llm_provider_with_openai_setting_returns_openai(mocker):
    mocker.patch("app.services.llm.get_settings", return_value=SimpleNamespace(llm_provider="openai"))

    provider = get_llm_provider()

    assert isinstance(provider, OpenAIProvider)
