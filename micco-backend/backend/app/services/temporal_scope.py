"""Explicit dates select a historical edition; upload recency never does."""
import re
from datetime import date
from fastapi import HTTPException


def requested_date(question, explicit=None):
    if explicit is not None:
        return explicit
    match=re.search(r'(?:as of|on|tại ngày|vào ngày|ngày)\s+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b',question,re.I)
    if not match:
        return None
    text=match.group(1)
    try:
        if '/' in text:
            day,month,year=map(int,text.split('/'));return date(year,month,day)
        return date.fromisoformat(text)
    except ValueError:
        raise HTTPException(status_code=400,detail='Ngày đối chiếu không hợp lệ')
