"""
LiteLLM Gateway Provider
========================
Generic LLM/Embedding providers backed by LiteLLM's unified API.

This is the catch-all path for any provider that doesn't need its own
hand-tuned implementation (see app/services/llm/__init__.py for which
provider names get their native class instead, e.g. "gemini"/"ollama").
Adding a new hosted provider (DeepSeek, Anthropic, OpenRouter, ...) only
needs: LLM_PROVIDER=<name>, LLM_MODEL_FAST=<model>, <NAME>_API_KEY=<key>
in .env — no new provider class.
"""
from __future__ import annotations

import asyncio
import random
import base64
import json
import logging
import re
from typing import AsyncGenerator, Optional

import litellm
import numpy as np

from app.services.llm.base import EmbeddingProvider, LLMProvider
from app.services.llm.types import LLMMessage, StreamChunk

logger = logging.getLogger(__name__)

# Our provider name -> LiteLLM's model-prefix, where it differs from the name itself.
_LITELLM_PREFIX = {
    "ollama": "ollama_chat",
}


def _get(obj, name: str, default=None):
    """Defensively read an attribute/key off a LiteLLM response object.

    LiteLLM's return shapes are inconsistent across versions/providers —
    sometimes a real object with attributes, sometimes a plain dict (e.g.
    ``litellm.rerank()`` returns ``results`` as dicts, not objects). Stream
    chunks/deltas/tool_calls can vary the same way, so every access here
    goes through this helper instead of assuming one shape.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
_TOOL_TAG_RE = re.compile(r"^<tool_call>\s*(.*?)\s*</tool_call>$", re.DOTALL)


def _tool_names(tools: list | None) -> set[str]:
    """Extract the set of registered tool names from an ``astream(tools=...)``
    payload. Defensive because each entry may be a dict (the usual OpenAI-
    style ``{"type": "function", "function": {"name": ..., ...}}``) or an
    object exposing the same shape via attributes.
    """
    names: set[str] = set()
    if not tools:
        return names
    for t in tools:
        fn = _get(t, "function")
        name = _get(fn, "name") if fn is not None else _get(t, "name")
        if isinstance(name, str) and name:
            names.add(name)
    return names


def _parse_fallback_tool_call(text: str, valid_tool_names: set[str]) -> dict | None:
    """Detect a tool call emitted as plain JSON text instead of a native
    ``tool_calls`` delta (some OpenAI-compatible backends, or a model under
    prompt pressure, do this even with function-calling enabled).

    Only matches when the text — after optionally unwrapping a
    ``<tool_call>...</tool_call>`` tag or a ```json fence — IS, in its
    entirety, a ``{"name": ..., "arguments": {...}}`` object. This must
    NEVER fire on text that merely contains JSON alongside real prose, or
    it would swallow legitimate answers.

    Two extra guards (both required, on top of the "whole text is JSON"
    check above) keep a genuinely valid answer that happens to look like
    JSON — e.g. the user asked for the reply as a JSON object — from being
    swallowed as a fake tool call:
      * ``name`` must be one of the tools actually registered for this
        call (``valid_tool_names``, from the live ``tools=`` argument).
        If no tools were passed at all, the fallback can never fire.
      * ``arguments``/``args`` must be present and a non-empty dict (or a
        JSON string that parses to one) — a tool call with no arguments
        is not a real fallback signal.
    """
    if not valid_tool_names:
        return None

    candidate = text.strip()
    m = _TOOL_TAG_RE.match(candidate)
    if m:
        candidate = m.group(1).strip()
    else:
        m = _FENCE_RE.match(candidate)
        if m:
            candidate = m.group(1).strip()

    if not (candidate.startswith("{") and candidate.endswith("}")):
        return None
    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    if not isinstance(name, str) or not name or name not in valid_tool_names:
        return None

    args = data.get("arguments")
    if args is None:
        args = data.get("args")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
    if not isinstance(args, dict) or not args:
        return None
    return {"name": name, "args": args}


def _prefixed_model(provider: str, model: str) -> str:
    if "/" in model:
        return model  # already fully-qualified (e.g. "openai/gpt-4.1-mini")
    prefix = _LITELLM_PREFIX.get(provider, provider)
    return f"{prefix}/{model}"


def _messages_payload(messages: list[LLMMessage], system_prompt: Optional[str]) -> list[dict]:
    out: list[dict] = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})

    for msg in messages:
        role = msg.role if msg.role in ("system", "user", "assistant") else "user"
        if msg.images:
            content: list[dict] = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            for img in msg.images:
                b64 = base64.b64encode(img.data).decode("utf-8")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{img.mime_type};base64,{b64}"},
                })
            out.append({"role": role, "content": content})
        else:
            out.append({"role": role, "content": msg.content})
    return out


class LiteLLMProvider(LLMProvider):
    """Text/vision generation via LiteLLM's unified completion() API."""

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        api_base: Optional[str] = None,
    ):
        self._provider = provider
        self._model = _prefixed_model(provider, model)
        self._api_key = api_key or None
        self._api_base = api_base

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        think: bool = False,
    ):
        payload = _messages_payload(messages, system_prompt)
        try:
            response = litellm.completion(
                model=self._model,
                messages=payload,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self._api_key,
                api_base=self._api_base,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning("Completion unavailable: %s", type(e).__name__)
            return ""

    async def acomplete(self, messages, *, temperature=0.0, max_tokens=4096, system_prompt=None, think=False):
        payload = _messages_payload(messages, system_prompt)
        for attempt in range(3):
            try:
                response = await litellm.acompletion(model=self._model, messages=payload,
                    temperature=temperature, max_tokens=max_tokens, api_key=self._api_key,
                    api_base=self._api_base, timeout=15, max_retries=0, num_retries=0)
                return response.choices[0].message.content or ""
            except Exception as error:
                retryable = getattr(error, 'status_code', None) in {429, 500, 502, 503, 504} or type(error).__name__ in {'Timeout', 'TimeoutError', 'APIConnectionError'}
                if not retryable or attempt == 2:
                    logger.warning("Completion unavailable: %s", type(error).__name__)
                    raise
                headers = getattr(getattr(error, 'response', None), 'headers', {}) or {}
                try: delay = float(headers.get('retry-after', 0))
                except (ValueError, TypeError): delay = 0
                await asyncio.sleep(min(5, max(delay, .5 * 2**attempt)) + random.uniform(0, .2))

    async def astream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        think: bool = False,
        tools: list | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        payload = _messages_payload(messages, system_prompt)
        full_text = ""
        # OpenAI-style streamed tool calls arrive as fragments keyed by
        # index — "arguments" is split across many chunks and must be
        # concatenated before it can be json.loads-ed, once the stream ends.
        tool_calls_acc: dict[int, dict] = {}
        try:
            kwargs = dict(
                model=self._model,
                messages=payload,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self._api_key,
                api_base=self._api_base,
                stream=True,
            )
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            stream = await litellm.acompletion(**kwargs)
            async for chunk in stream:
                choices = _get(chunk, "choices") or []
                if not choices:
                    continue
                delta = _get(choices[0], "delta")

                text = _get(delta, "content")
                if text:
                    full_text += text
                    yield StreamChunk(type="text", text=text)

                delta_tool_calls = _get(delta, "tool_calls")
                if delta_tool_calls:
                    for tc in delta_tool_calls:
                        idx = _get(tc, "index", 0) or 0
                        fn = _get(tc, "function")
                        name = _get(fn, "name")
                        args_piece = _get(fn, "arguments")
                        entry = tool_calls_acc.setdefault(idx, {"name": "", "arguments": ""})
                        if name and not entry["name"]:
                            entry["name"] = name
                        if args_piece:
                            entry["arguments"] += args_piece

            if tool_calls_acc:
                # Native tool-calling path.
                for idx in sorted(tool_calls_acc.keys()):
                    entry = tool_calls_acc[idx]
                    name = entry.get("name") or ""
                    if not name:
                        continue
                    args_str = entry.get("arguments") or ""
                    try:
                        args = json.loads(args_str) if args_str.strip() else {}
                    except (json.JSONDecodeError, TypeError, ValueError):
                        # Malformed arguments must not kill the stream —
                        # just drop this tool call.
                        logger.warning(
                            f"LiteLLM: failed to parse tool call arguments for "
                            f"{name!r}: {args_str!r}"
                        )
                        continue
                    yield StreamChunk(type="function_call", function_call={"name": name, "args": args})
            elif full_text.strip() and tools:
                # Fallback path — see _parse_fallback_tool_call docstring.
                # Text was already streamed live above; chat_agent.py's
                # token_rollback mechanism discards it client-side once it
                # sees the function_call chunk below.
                parsed = _parse_fallback_tool_call(full_text, _tool_names(tools))
                if parsed:
                    yield StreamChunk(type="function_call", function_call=parsed)
        except Exception as e:
            logger.warning("Streaming unavailable: %s", type(e).__name__)
            yield StreamChunk(type="text", text="")

    def supports_vision(self) -> bool:
        try:
            return bool(litellm.supports_vision(model=self._model))
        except Exception:
            return False

    def supports_thinking(self) -> bool:
        return False


class LiteLLMEmbeddingProvider(EmbeddingProvider):
    """Text embedding via LiteLLM's unified embedding() API."""

    _BATCH_SIZE = 100

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        dimension: int = 1536,
        api_base: Optional[str] = None,
    ):
        self._model = _prefixed_model(provider, model)
        self._api_key = api_key or None
        self._api_base = api_base
        self._dimension = dimension

    def embed_sync(self, texts: list[str]) -> np.ndarray:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self._BATCH_SIZE):
            batch = texts[i : i + self._BATCH_SIZE]
            try:
                result = litellm.embedding(
                    model=self._model,
                    input=batch,
                    api_key=self._api_key,
                    api_base=self._api_base,
                )
                for item in result.data:
                    all_embeddings.append(item["embedding"])
            except Exception as e:
                logger.error(f"LiteLLM embedding failed for batch {i} ({self._model}): {e}")
                for _ in batch:
                    all_embeddings.append([0.0] * self._dimension)

        return np.array(all_embeddings, dtype=np.float32)

    def get_dimension(self) -> int:
        return self._dimension
