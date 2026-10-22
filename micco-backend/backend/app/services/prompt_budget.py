"""Budget the full provider prompt, not only the number of history messages."""
from app.services.conversation_context import _positive_env
from fastapi import HTTPException
from app.services.conversation_context import token_cost, clip_to_budget


def context_limit():
    return max(4096, _positive_env('CHAT_CONTEXT_TOKEN_BUDGET', 32768))


def output_limit():
    return min(4096, max(256, _positive_env('CHAT_CONTEXT_OUTPUT_RESERVE', 4096)))


def check_prompt(messages, system_prompt, *, output_tokens=None):
    output = output_tokens or output_limit()
    # Inline images are bounded by the application separately; reserve vision
    # capacity rather than treating binary input as zero tokens.
    used = token_cost(system_prompt) + sum(token_cost(m.content or '') + 32 + 4096 * len(m.images or []) for m in messages)
    if used + output > context_limit():
        raise HTTPException(status_code=413, detail='Ngữ cảnh vượt giới hạn xử lý; hãy thu hẹp tài liệu hoặc rút gọn câu hỏi.')
    return used


def fit_source_context(context, question, system_prompt, history):
    """Retrieval is lower priority than preserving question/system boundaries."""
    used = token_cost(question) + token_cost(system_prompt) + sum(token_cost(m.get('content',''))+32 for m in history)
    remaining = max(0, context_limit() - output_limit() - used - 2048)
    return clip_to_budget(context, remaining)
