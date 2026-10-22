"""Social turns bypass retrieval; mixed or business turns require evidence."""
import re
import unicodedata

_GREETING_REPLY = 'Xin chào! Bạn muốn tìm thông tin gì trong kho tri thức?'
_THANKS_REPLY = 'Rất vui được hỗ trợ bạn.'
_BYE_REPLY = 'Chào bạn!'
_IDENTITY_REPLY = (
    'Tôi là trợ lý AI của MICCO, hỗ trợ tra cứu và hỏi đáp dựa trên kho tri thức nội bộ. '
    'Bạn muốn tìm thông tin gì?'
)
_CAPABILITY_REPLY = (
    'Tôi có thể tra cứu tài liệu, quy trình, quy định và tổng hợp câu trả lời kèm nguồn '
    'từ kho tri thức nội bộ. Bạn muốn hỏi về nội dung gì?'
)


def _normalize(message):
    normalized = re.sub(r'[^\w\s]', '', unicodedata.normalize('NFKC', message or '').casefold())
    return ' '.join(normalized.split())


def social_reply(message):
    normalized = _normalize(message)
    if not normalized:
        return None
    words = normalized.split()
    if normalized in {
        'hi', 'hello', 'hey', 'xin chào', 'chào', 'chao', 'xin chao', 'good morning',
        'good afternoon', 'good evening', 'chào bạn', 'chao ban', 'hello bạn', 'hi bạn',
    }:
        return _GREETING_REPLY
    if normalized in {'cảm ơn', 'cam on', 'thanks', 'thank you', 'cảm ơn bạn', 'cam on ban'}:
        return _THANKS_REPLY
    if normalized in {'tạm biệt', 'tam biet', 'bye', 'goodbye', 'chào nhé', 'chao nhe'}:
        return _BYE_REPLY
    if len(words) > 10:
        return None
    identity = (
        'bạn là ai', 'ban la ai', 'bạn tên gì', 'ban ten gi', 'bạn là gì', 'ban la gi',
        'giới thiệu về bạn', 'gioi thieu ve ban', 'who are you',
    )
    capability = (
        'bạn có thể làm gì', 'ban co the lam gi', 'bạn làm được gì', 'ban lam duoc gi',
        'bạn giúp được gì', 'ban giup duoc gi', 'what can you do',
        'bạn có những chức năng gì', 'ban co nhung chuc nang gi',
    )
    if any(phrase in normalized for phrase in identity):
        return _IDENTITY_REPLY
    if any(phrase in normalized for phrase in capability):
        return _CAPABILITY_REPLY
    return None
