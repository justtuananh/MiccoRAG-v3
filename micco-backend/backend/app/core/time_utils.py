"""Normalize legacy timestamptz and timestamp values at model boundaries."""
from datetime import timezone


def utc_naive(value):
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
