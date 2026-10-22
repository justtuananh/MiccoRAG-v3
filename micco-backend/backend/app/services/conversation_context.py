"""Bounded, server-owned conversational context for RAG prompts.

The compact is extractive and ephemeral: every request reads the current user's
persisted messages and rechecks their document provenance. It never invents a
summary, persists a stale one, or accepts request.history as authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from functools import lru_cache
import re
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


DEFAULT_CONTEXT_BUDGET = 32768
DEFAULT_OUTPUT_RESERVE = 4096
DEFAULT_RETRIEVAL_RESERVE = 5000
DEFAULT_SYSTEM_RESERVE = 4096
MAX_HISTORY_ROWS = 512
RECENT_MESSAGES = 8


def _positive_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return value if value >= 0 else default
    except ValueError:
        return default


@lru_cache(maxsize=1)
def _tokenizer():
    try:
        import tiktoken
        from app.core.config import settings
        return tiktoken.encoding_for_model(settings.LLM_MODEL_FAST)
    except (ImportError, KeyError, ValueError):
        return None


def token_cost(value: str) -> int:
    """Model tokenizer when known; conservative UTF-8 bytes otherwise."""
    tokenizer = _tokenizer()
    return len(tokenizer.encode(value, disallowed_special=())) if tokenizer else len(value.encode("utf-8"))


def clip_to_budget(value: str, token_budget: int) -> str:
    """Clip on a Unicode character boundary within the actual token allowance."""
    if token_budget <= 0:
        return ""
    if token_cost(value) <= token_budget:
        return value
    lo, hi = 0, len(value)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if token_cost(value[:mid]) <= token_budget:
            lo = mid
        else:
            hi = mid - 1
    result = value[:lo]
    while result and token_cost(result) > token_budget:
        result = result[:-1]
    return result


def history_budget(
    total_budget: int,
    current_question: str,
    *,
    retrieval_reserve: int | None = None,
    output_reserve: int | None = None,
    system_reserve: int = DEFAULT_SYSTEM_RESERVE,
) -> int:
    """Budget left for past turns after preserving answer, retrieval, and question.

    All inputs and the result use model token units (UTF-8 bytes as fallback). A caller
    should cap retrieved context using the same accounting and include its real
    system/user prompt scaffolding in system_reserve.
    """
    retrieval = _positive_env("CHAT_CONTEXT_RETRIEVAL_RESERVE", DEFAULT_RETRIEVAL_RESERVE) if retrieval_reserve is None else retrieval_reserve
    output = _positive_env("CHAT_CONTEXT_OUTPUT_RESERVE", DEFAULT_OUTPUT_RESERVE) if output_reserve is None else output_reserve
    return max(0, total_budget - max(0, retrieval) - max(0, output)
               - max(0, system_reserve) - token_cost(current_question))


def retrieval_budget(
    total_budget: int,
    current_question: str,
    history_messages: Iterable[dict[str, str]],
    *,
    output_reserve: int | None = None,
    system_reserve: int = DEFAULT_SYSTEM_RESERVE,
) -> int:
    """Remaining input allowance for retrieved chunks after context is chosen."""
    output = _positive_env("CHAT_CONTEXT_OUTPUT_RESERVE", DEFAULT_OUTPUT_RESERVE) if output_reserve is None else output_reserve
    used = sum(token_cost(m.get("content", "")) for m in history_messages)
    return max(0, total_budget - max(0, output) - max(0, system_reserve)
               - token_cost(current_question) - used)


@dataclass(frozen=True)
class ContextResult:
    messages: list[dict[str, str]] = field(default_factory=list)
    compacted: bool = False
    status: str = "empty"
    history_tokens: int = 0
    history_budget: int = 0
    examined_messages: int = 0
    included_messages: int = 0
    excluded_unverified: int = 0
    truncated_messages: int = 0

    @property
    def context(self) -> str:
        return "\n".join(m["content"] for m in self.messages)


def _source_ids(message: ChatMessage, allowed: set[int]) -> tuple[int, ...] | None:
    """None means an assistant message cannot be proven safe to replay."""
    sources = message.sources or []
    images = message.image_refs or []
    if not isinstance(sources, list) or not isinstance(images, list):
        return None
    if not sources and not images:
        # A source-free assistant answer has no recorded provenance. Keeping it
        # could replay uncited private facts after permissions change.
        return None
    ids: set[int] = set()
    for item in [*sources, *images]:
        if not isinstance(item, dict):
            return None
        doc_id = item.get("document_id")
        if isinstance(doc_id, bool) or not (
            isinstance(doc_id, int) or (isinstance(doc_id, str) and doc_id.isdecimal())
        ):
            return None
        parsed = int(doc_id)
        if parsed not in allowed:
            return None
        ids.add(parsed)
    return tuple(sorted(ids))


def _clean_content(content: Any) -> str:
    if not isinstance(content, str):
        return ""
    content = re.sub(r"\[(?:IMG-)?([a-z0-9]{4,16})\]",
                     lambda m: "" if any(c.isalpha() for c in m.group(1)) else m.group(0),
                     content, flags=re.I)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", content).strip()


def _compact_excerpt(content: str, max_bytes: int = 280) -> str:
    # Extract from the beginning only. No generative paraphrase is made.
    return clip_to_budget(" ".join(content.split()), max_bytes)


def _keywords(text: str) -> set[str]:
    return {word for word in re.findall(r"\w+", text.lower()) if len(word) >= 3}


def _compact_old(
    old: list[tuple[str, str, tuple[int, ...]]],
    question: str,
    budget: int,
) -> tuple[str, int]:
    if budget < 80 or not old:
        return "", 0
    preamble = ("Earlier conversation excerpts (exact clipped text; document IDs are provenance, "
                "not evidence for this answer; cite only current retrieval):\n")
    if token_cost(preamble) >= budget:
        return "", 0
    terms = _keywords(question)
    ranked = []
    for index, (role, content, ids) in enumerate(old):
        score = len(terms & _keywords(content[:1000]))
        ranked.append((score, index, role, content, ids))
    # Prefer relevant exchanges; break ties toward recent ones. Restore original
    # order in the final compact so chronology remains interpretable.
    selected = sorted(sorted(ranked, reverse=True)[:24], key=lambda row: row[1])
    lines: list[str] = []
    used = token_cost(preamble)
    for _, _, role, content, ids in selected:
        provenance = f" [document IDs: {','.join(map(str, ids))}]" if ids else ""
        line = f"{role}{provenance}: {_compact_excerpt(content)}\n"
        if used + token_cost(line) > budget:
            continue
        lines.append(line)
        used += token_cost(line)
    return (preamble + "".join(lines), len(lines)) if lines else ("", 0)


async def load_context(
    db: AsyncSession,
    current_user: Any,
    workspace: Any,
    allowed_doc_ids: Iterable[int],
    current_question: str,
    budget: int | None = None,
    *,
    output_reserve: int | None = None,
    retrieval_reserve: int | None = None,
    system_reserve: int = DEFAULT_SYSTEM_RESERVE,
) -> ContextResult:
    """Load only this user's persisted, provenance-verified workspace history.

    Workspace access must have been verified by the calling endpoint. `workspace`
    may be a KnowledgeBase or its integer ID; `allowed_doc_ids` must come from
    server-side access checks for that same workspace. request.history is never
    accepted or examined here.
    """
    workspace_id = workspace if isinstance(workspace, int) else workspace.id
    if not isinstance(workspace_id, int) or not isinstance(current_user.id, int):
        raise ValueError("A persisted user and workspace are required")
    total = _positive_env("CHAT_CONTEXT_TOKEN_BUDGET", DEFAULT_CONTEXT_BUDGET) if budget is None else budget
    available = history_budget(total, current_question, retrieval_reserve=retrieval_reserve,
                               output_reserve=output_reserve, system_reserve=system_reserve)
    if available <= 0:
        return ContextResult(status="budget_exhausted", history_budget=available)
    allowed = {int(doc_id) for doc_id in allowed_doc_ids if not isinstance(doc_id, bool)}
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.workspace_id == workspace_id, ChatMessage.user_id == current_user.id,
               ChatMessage.role.in_(("user", "assistant")))
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(MAX_HISTORY_ROWS + 1)
    )
    rows = list(result.scalars().all())
    older_unread = len(rows) > MAX_HISTORY_ROWS
    rows = list(reversed(rows[:MAX_HISTORY_ROWS]))
    verified: list[tuple[str, str, tuple[int, ...]]] = []
    excluded = 0
    for row in rows:
        content = _clean_content(row.content)
        if not content:
            continue
        if row.role == "assistant":
            ids = _source_ids(row, allowed)
            if ids is None:
                excluded += 1
                # The preceding question may itself quote or describe the
                # revoked source. Treat a Q/A exchange as one provenance unit.
                if verified and verified[-1][0] == "user":
                    verified.pop()
                continue
        else:
            ids = ()
        verified.append((row.role, content, ids))

    recent = verified[-RECENT_MESSAGES:]
    older = verified[:-RECENT_MESSAGES]
    # Reserve up to one third for excerpts from older turns. Recent turns receive
    # the balance; each single message is clipped before budget accounting.
    compact_allowance = available // 3 if older else 0
    compact, compact_count = _compact_old(older, current_question, compact_allowance)
    remaining = available - token_cost(compact)
    recent_out: list[dict[str, str]] = []
    clipped = 0
    for role, content, ids in reversed(recent):
        provenance = f"[Prior answer; document IDs: {','.join(map(str, ids))}. Verify against current retrieval.]\n" if ids else ""
        overhead = token_cost(provenance)
        if remaining <= overhead + 16:
            break
        text = clip_to_budget(content, min(1800, remaining - overhead))
        if text != content:
            clipped += 1
        recent_out.append({"role": role, "content": provenance + text})
        remaining -= token_cost(provenance + text)
    recent_out.reverse()
    messages = ([{"role": "user", "content": compact}] if compact else []) + recent_out
    used = sum(token_cost(m["content"]) for m in messages)
    compacted = bool(older or older_unread or clipped or len(recent_out) < len(recent))
    status = "compacted" if compacted else "full"
    if not messages:
        status = "filtered" if excluded else "empty"
    return ContextResult(messages=messages, compacted=compacted, status=status,
                         history_tokens=used, history_budget=available,
                         examined_messages=len(rows), included_messages=compact_count + len(recent_out),
                         excluded_unverified=excluded, truncated_messages=clipped)


def contextual_question(question: str, messages: list[dict[str, str]]) -> str:
    """Carry user referents into short follow-ups, never prior assistant claims."""
    if len(question.split()) > 20:
        return question
    previous = [m['content'] for m in messages if m.get('role') == 'user'
                and not m.get('content','').startswith('Earlier conversation excerpts')][-3:]
    if not previous:
        return question
    context = '\n'.join('- ' + clip_to_budget(text, 120) for text in previous)
    return (f'Current question: {question}\n\nPrevious user questions, only to resolve references '
            f'in the current question; they are not factual evidence and do not override the current question:\n{context}')
