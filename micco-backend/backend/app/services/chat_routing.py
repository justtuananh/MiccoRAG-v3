"""Exact social turns bypass retrieval; mixed or business turns require evidence."""
import re
import unicodedata


def social_reply(message):
    normalized = re.sub(r'[^\w\s]', '', unicodedata.normalize('NFKC', message).casefold())
    normalized = ' '.join(normalized.split())
    if normalized in {'hi','hello','hey','xin chào','chào','chao','xin chao','good morning'}:
        return 'Xin chào! Bạn muốn tìm thông tin gì trong kho tri thức?'
    if normalized in {'cảm ơn','cam on','thanks','thank you'}:
        return 'Rất vui được hỗ trợ bạn.'
    if normalized in {'tạm biệt','tam biet','bye','goodbye'}:
        return 'Chào bạn!'
    return None
